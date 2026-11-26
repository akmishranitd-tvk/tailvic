import re
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
from werkzeug.security import generate_password_hash
from app import create_app, IST
from content import ARTICLES
from pricing import DOG_PRICES, CAT_PRICES, price_for
from html.parser import HTMLParser
import json

class SelectOptions(HTMLParser):
    def __init__(self,html):
        super().__init__()
        self.current=None
        self.option=None
        self.text=''
        self.options={}
        self.feed(html)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='select':
            self.current=attrs.get('name')
            self.options[self.current]=[]
        if tag=='option' and self.current:
            self.option=attrs.get('value','')
            self.text=''
    def handle_data(self,data):
        if self.option is not None:
            self.text+=data
    def handle_endtag(self,tag):
        if tag=='option' and self.current and self.option is not None:
            self.options[self.current].append((self.option,self.text))
            self.option=None
        if tag=='select':
            self.current=None

class TailvicTests(unittest.TestCase):
    def setUp(self):
        temp_root=Path(__file__).resolve().parents[1]/'test-results'
        temp_root.mkdir(exist_ok=True)
        self.temp_path=temp_root/('unit-'+uuid.uuid4().hex)
        self.temp_path.mkdir()
        self.app=create_app({'TESTING':True,'DATABASE':str(self.temp_path/'test.sqlite'),'SECRET_KEY':'isolated-test-secret'})
        self.customer=self.app.test_client()
        self.other=self.app.test_client()
        self.admin=self.app.test_client()
        with self.app.app_context():
            self.app.get_db().execute("INSERT INTO users(id,name,email,phone,password,role) VALUES(1,'Owner','owner@example.test','9876543210',?,'admin')",(generate_password_hash('test-owner-password'),))
        self.login_admin()

    def tearDown(self):
        for file in self.temp_path.iterdir():
            file.unlink()
        self.temp_path.rmdir()

    def csrf(self,client):
        client.get('/')
        with client.session_transaction() as s:
            return s['csrf']

    def post(self,client,path,data):
        return client.post(path,data={'csrf':self.csrf(client),**data})

    def login_admin(self):
        self.post(self.admin,'/account/',dict(action='login',email='owner@example.test',password='test-owner-password'))

    def details(self,**extra):
        data=dict(name='Pet parent',email='parent@example.test',phone='9876543210',pet_name='Milo',species='dog',size='medium',coat='double',service='bath-brush',address='Gurgaon test address',pin='122101',notes='Gentle introduction please',preferred=(datetime.now(IST)+timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),consent='on',mode='request')
        data.update(extra)
        return data

    def request_booking(self,client=None):
        response=self.post(client or self.customer,'/book/',self.details())
        self.assertEqual(response.status_code,302)
        return response.location.split('/')[-2]

    def test_public_pages_and_headers(self):
        for path in ['/','/services/','/services/dog-grooming/','/services/cat-grooming/','/packages/','/care-guides/','/care-guides/prepare-for-home-grooming/','/care-guides/breeds/indie-dog/','/our-groomers/','/areas/','/wellness/','/membership/','/privacy/','/terms/','/faqs/','/book/','/account/','/robots.txt','/sitemap.xml']:
            with self.subTest(path=path):
                r=self.customer.get(path)
                self.assertEqual(r.status_code,200)
                self.assertEqual(r.headers['X-Frame-Options'],'SAMEORIGIN')
                self.assertIn("frame-ancestors 'self'",r.headers['Content-Security-Policy'])
        self.assertEqual(self.customer.get('/does-not-exist/').status_code,404)

    def test_csrf_and_admin_access(self):
        self.assertEqual(self.customer.post('/book/',data=self.details()).status_code,400)
        self.assertEqual(self.customer.get('/admin/').status_code,302)
        self.post(self.customer,'/account/',dict(action='register',name='Customer',email='customer@example.test',phone='9876543210',password='correct-customer-password'))
        self.assertEqual(self.customer.get('/admin/').status_code,403)

    def test_ownership_and_guest_account_adoption(self):
        bid=self.request_booking()
        self.assertEqual(self.other.get('/booking/'+bid+'/').status_code,404)
        self.post(self.customer,'/account/',dict(action='register',name='Pet parent',email='parent@example.test',phone='9876543210',password='correct-customer-password'))
        self.assertIn(bid,self.customer.get('/account/').get_data(as_text=True))
        with self.app.app_context():
            record=self.app.get_db().execute('SELECT password FROM users WHERE email=?',('parent@example.test',)).fetchone()['password']
            self.assertNotEqual(record,'correct-customer-password')

    def test_booking_quote_upi_verification(self):
        bid=self.request_booking()
        self.assertNotIn('upi://pay?',self.customer.get('/booking/'+bid+'/').get_data(as_text=True))
        self.assertEqual(self.post(self.customer,'/booking/'+bid+'/',dict(action='accept')).status_code,400)
        quote=dict(action='quote',bid=bid,base='999',travel='100',tax='147.44',confirmed_starts=self.details()['preferred'])
        self.assertEqual(self.post(self.admin,'/admin/',quote).status_code,302)
        self.assertEqual(self.post(self.customer,'/booking/'+bid+'/',dict(action='accept')).status_code,302)
        page=self.customer.get('/booking/'+bid+'/').get_data(as_text=True)
        self.assertIn('7845475769@upi',page)
        self.assertIn('1,246.44',page)
        qr=self.customer.get('/booking/'+bid+'/payment-qr.svg')
        self.assertEqual(qr.status_code,200)
        self.assertIn(b'<svg',qr.data)
        self.assertEqual(self.other.get('/booking/'+bid+'/payment-qr.svg').status_code,404)
        self.post(self.customer,'/booking/'+bid+'/',dict(action='payment',utr='123456789012'))
        self.assertIn('awaiting manual verification',self.customer.get('/booking/'+bid+'/').get_data(as_text=True))
        self.assertEqual(self.post(self.customer,'/admin/',dict(action='verify_payment',bid=bid)).status_code,302)
        self.post(self.admin,'/admin/',dict(action='verify_payment',bid=bid))
        self.assertIn('Payment verified',self.customer.get('/booking/'+bid+'/').get_data(as_text=True))

    def test_slot_double_booking_and_cancel_release(self):
        starts=(datetime.now(IST)+timedelta(days=2)).replace(minute=0,second=0,microsecond=0).isoformat(timespec='minutes')
        self.post(self.admin,'/admin/',dict(action='slot',starts=starts))
        slot=self.customer.get('/api/slots/').json[0]
        d=self.details();d.update(mode='slot',slot_id=str(slot['id']))
        r=self.post(self.customer,'/book/',d)
        self.assertEqual(r.status_code,302)
        bid=r.location.split('/')[-2]
        self.assertEqual(self.customer.get('/api/slots/').json,[])
        r=self.post(self.other,'/book/',d)
        self.assertEqual(r.status_code,200)
        self.assertIn('just reserved',r.get_data(as_text=True))
        self.post(self.customer,'/booking/'+bid+'/',dict(action='cancel'))
        self.assertEqual(len(self.customer.get('/api/slots/').json),1)

    def test_simultaneous_slot_reservations(self):
        starts=(datetime.now(IST)+timedelta(days=2)).replace(minute=0,second=0,microsecond=0).isoformat(timespec='minutes')
        self.post(self.admin,'/admin/',dict(action='slot',starts=starts))
        sid=self.customer.get('/api/slots/').json[0]['id']
        def reserve(index):
            c=self.app.test_client()
            d=self.details();d.update(mode='slot',slot_id=str(sid))
            return self.post(c,'/book/',d).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(reserve,range(2)))
        self.assertEqual(sorted(results),[200,302])
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT COUNT(*) FROM bookings WHERE slot_id=?',(sid,)).fetchone()[0],1)

    def test_request_quotes_cannot_overlap(self):
        one=self.request_booking()
        two=self.request_booking(self.other)
        q=dict(action='quote',base='999',travel='100',tax='0',confirmed_starts=self.details()['preferred'])
        self.assertEqual(self.post(self.admin,'/admin/',dict(q,bid=one)).status_code,302)
        r=self.post(self.admin,'/admin/',dict(q,bid=two))
        self.assertEqual(r.status_code,200)
        self.assertIn('already reserved',r.get_data(as_text=True))

    def test_all_approved_package_prices_are_selected_by_size_or_coat(self):
        sizes=('small','medium','large','giant')
        dog_expected={
            'bath-brush':(99900,119900,149900,189900),
            'hygiene-groom':(129900,159900,199900,249900),
            'full-groom':(179900,219900,269900,329900),
            'signature-coat-spa':(229900,269900,329900,399900),
        }
        for service,values in dog_expected.items():
            for size,value in zip(sizes,values):
                with self.subTest(species='dog',service=service,size=size):
                    self.assertEqual(price_for('dog',service,size=size),value)
        cat_expected={
            'cat-coat-refresh':(99900,129900),
            'cat-hygiene-groom':(139900,169900),
            'cat-full-coat-groom':(189900,239900),
        }
        for service,values in cat_expected.items():
            for coat,value in zip(('short','long'),values):
                with self.subTest(species='cat',service=service,coat=coat):
                    self.assertEqual(price_for('cat',service,coat=coat),value)
        self.assertIsNone(price_for('dog','express-care',size='small'))
        self.assertIsNone(price_for('cat','express-care',coat='short'))

    def test_package_prices_are_published_on_pricing_and_category_pages(self):
        pages={
            '/packages/':(*DOG_PRICES.values(),*CAT_PRICES.values()),
            '/services/':(*DOG_PRICES.values(),*CAT_PRICES.values()),
            '/services/dog-grooming/':tuple(DOG_PRICES.values()),
            '/services/cat-grooming/':tuple(CAT_PRICES.values()),
        }
        for path,matrices in pages.items():
            with self.subTest(path=path):
                page=self.customer.get(path).get_data(as_text=True)
                for prices in matrices:
                    for amount in prices.values():
                        self.assertIn('₹'+f'{amount/100:,.0f}',page)
        for path in ('/services/','/packages/'):
            page=self.customer.get(path).get_data(as_text=True)
            for package in ('Bath &amp; Brush','Hygiene Groom','Full Style Groom','Signature Coat Spa','Coat Refresh','Full Coat Groom'):
                self.assertIn(package,page)

    def test_booking_snapshots_price_for_new_requests_and_preserves_existing_quote(self):
        cases=[('dog',service,size,'short',price) for service,values in DOG_PRICES.items() for size,price in values.items()]
        cases += [('cat',service,'medium',coat,price) for service,values in CAT_PRICES.items() for coat,price in values.items()]
        cases += [('dog','express-care','small','short',None)]
        for species,service,size,coat,expected in cases:
            with self.subTest(species=species,service=service,size=size,coat=coat):
                response=self.post(self.customer,'/book/',self.details(species=species,service=service,size=size,coat=coat))
                self.assertEqual(response.status_code,302)
                bid=response.location.split('/')[-2]
                with self.app.app_context():
                    row=self.app.get_db().execute('SELECT base FROM bookings WHERE id=?',(bid,)).fetchone()
                    self.assertEqual(row['base'],expected)
                    self.app.get_db().execute('DELETE FROM limits')
        historical=self.request_booking()
        with self.app.app_context():
            d=self.app.get_db()
            d.execute("UPDATE bookings SET status='confirmed',base=88800,total=88800 WHERE id=?",(historical,))
            self.app.init_db()
            row=d.execute('SELECT status,base,total FROM bookings WHERE id=?',(historical,)).fetchone()
            self.assertEqual(tuple(row),('confirmed',88800,88800))

    def test_editing_and_xss_escaping(self):
        self.post(self.admin,'/admin/',dict(action='service',slug='bath-brush',name='Fresh Bath',price='800',description='<script>alert(1)</script>',duration='60 minutes',includes='Bath\nBrush'))
        page=self.customer.get('/services/').get_data(as_text=True)
        self.assertIn('Bath &amp; Brush',page)
        self.assertIn('₹999',page)
        self.assertNotIn('₹800',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertNotIn('<script>alert(1)</script>',page)
        self.post(self.admin,'/admin/',dict(action='article',slug='choose-a-grooming-package',title='Updated guide',summary='A useful summary',body='Original text\nAnother paragraph'))
        self.assertIn('Updated guide',self.customer.get('/care-guides/choose-a-grooming-package/').get_data(as_text=True))

    def test_analytics_consent(self):
        token=self.csrf(self.customer)
        headers={'X-CSRF-Token':token}
        self.customer.post('/api/events/',json=dict(event='page_view',path='/'),headers=headers)
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT COUNT(*) FROM events').fetchone()[0],0)
        self.customer.set_cookie('tailvic_analytics','yes')
        self.customer.post('/api/events/',json=dict(event='page_view',path='/'),headers=headers)
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
        self.assertEqual(self.customer.post('/api/events/',json=dict(event='fake_revenue',path='/'),headers=headers).status_code,400)

    def test_species_validation_and_required_consent(self):
        d=self.details();d.update(species='cat',service='bath-brush')
        self.assertIn('suited to your dog or cat',self.post(self.customer,'/book/',d).get_data(as_text=True))
        d=self.details();d.pop('consent')
        self.assertEqual(self.post(self.customer,'/book/',d).status_code,200)

    def test_past_time_rejected_and_slot_overlap_blocked(self):
        d=self.details();d['preferred']='2020-01-01T12:00'
        self.assertIn('future preferred time',self.post(self.customer,'/book/',d).get_data(as_text=True))
        start=(datetime.now(IST)+timedelta(days=2)).replace(minute=0,second=0,microsecond=0)
        self.post(self.admin,'/admin/',dict(action='slot',starts=start.isoformat(timespec='minutes')))
        r=self.post(self.admin,'/admin/',dict(action='slot',starts=(start+timedelta(minutes=30)).isoformat(timespec='minutes')))
        self.assertIn('overlaps',r.get_data(as_text=True))

    def test_customer_cannot_change_quote_or_verify_payment(self):
        bid=self.request_booking()
        self.post(self.admin,'/admin/',dict(action='quote',bid=bid,base='700',travel='100',tax='0',confirmed_starts=self.details()['preferred']))
        self.post(self.customer,'/booking/'+bid+'/',dict(action='accept',total='1'))
        with self.app.app_context():
            b=self.app.get_db().execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
            self.assertEqual(b['total'],80000)
            self.assertEqual(b['payment'],'unpaid')
        self.assertEqual(self.post(self.customer,'/booking/'+bid+'/',dict(action='verify_payment')).status_code,400)

    def test_species_specific_size_examples_and_service_menu(self):
        dog=SelectOptions(self.customer.get('/book/').get_data(as_text=True)).options
        self.assertEqual([v for v,label in dog['size']],['small','medium','large','giant'])
        self.assertIn('Chihuahua',dog['size'][0][1])
        self.assertIn('Great Dane',dog['size'][-1][1])
        self.assertEqual([v for v,label in dog['service']],['bath-brush','hygiene-groom','full-groom','signature-coat-spa','express-care'])
        cat=SelectOptions(self.customer.get('/book/?service=cat-coat-refresh').get_data(as_text=True)).options
        self.assertEqual([v for v,label in cat['size']],['small','medium','large'])
        self.assertIn('Maine Coon',cat['size'][-1][1])
        self.assertEqual([v for v,label in cat['service']],['cat-coat-refresh','cat-hygiene-groom','cat-full-coat-groom','express-care'])

    def test_cat_giant_category_is_rejected_server_side(self):
        d=self.details();d.update(species='cat',service='cat-coat-refresh',size='giant')
        r=self.post(self.customer,'/book/',d)
        self.assertEqual(r.status_code,200)
        self.assertIn('size category available',r.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT COUNT(*) FROM bookings').fetchone()[0],0)

    def applicant(self):
        return dict(name='Sample Groomer',email='groomer@example.test',phone='9876543210',city='Gurgaon',experience='1-3',species='both',availability='Next month, weekdays',qualification='Professional grooming course',portfolio='https://example.test/portfolio',message='Patient handling and coat care.',consent='on')

    def test_application_saved_and_reviewed_privately(self):
        r=self.post(self.customer,'/careers/',self.applicant())
        self.assertEqual(r.status_code,302)
        receipt=self.customer.get(r.location).get_data(as_text=True)
        self.assertIn('APPLICATION RECEIVED',receipt)
        reference=re.search(r'TV-J-[A-F0-9]{10}',receipt).group(0)
        self.assertNotIn('groomer@example.test',self.other.get('/careers/').get_data(as_text=True))
        self.assertEqual(self.other.get('/admin/#applications').status_code,302)
        owner=self.admin.get('/admin/').get_data(as_text=True)
        self.assertIn('groomer@example.test',owner)
        self.assertIn(reference,owner)
        self.assertEqual(self.post(self.admin,'/admin/',dict(action='application_status',application_id=reference,status='reviewing',section='applications')).status_code,302)
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT status FROM applications WHERE id=?',(reference,)).fetchone()['status'],'reviewing')
        self.assertNotIn('APPLICATION RECEIVED',self.customer.get('/careers/').get_data(as_text=True))

    def test_application_validation_and_csrf(self):
        self.assertEqual(self.customer.post('/careers/',data=self.applicant()).status_code,400)
        for extra in ({'consent':''},{'portfolio':'javascript:alert(1)'},{'experience':'invented'},{'phone':'123'}):
            data=self.applicant();data.update(extra)
            self.assertEqual(self.post(self.customer,'/careers/',data).status_code,200)
        with self.app.app_context():
            self.assertEqual(self.app.get_db().execute('SELECT COUNT(*) FROM applications').fetchone()[0],0)

    def test_application_text_is_escaped_and_status_is_validated(self):
        data=self.applicant();data['message']='<script>alert(1)</script>'
        self.post(self.customer,'/careers/',data)
        with self.app.app_context():
            reference=self.app.get_db().execute('SELECT id FROM applications').fetchone()['id']
        owner=self.admin.get('/admin/').get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',owner)
        self.assertNotIn('<script>alert(1)</script>',owner)
        r=self.post(self.admin,'/admin/',dict(action='application_status',application_id=reference,status='hired'))
        self.assertIn('valid review status',r.get_data(as_text=True))

    def test_new_articles_and_refinement_preserve_owner_edits(self):
        with self.app.app_context():
            d=self.app.get_db()
            article=json.loads(d.execute("SELECT data FROM articles WHERE slug='prepare-for-home-grooming'").fetchone()['data'])
            article.update(title='Their first home groom. Your easy checklist.',summary='Owner-written summary',body='Owner-written article')
            d.execute("UPDATE articles SET data=? WHERE slug='prepare-for-home-grooming'",(json.dumps(article),))
            service=json.loads(d.execute("SELECT data FROM services WHERE slug='bath-brush'").fetchone()['data'])
            service.update(description='Owner-written service',price=90000)
            d.execute("UPDATE services SET data=? WHERE slug='bath-brush'",(json.dumps(service),))
            self.app.init_db()
            self.app.init_db()
            updated=json.loads(d.execute("SELECT data FROM articles WHERE slug='prepare-for-home-grooming'").fetchone()['data'])
            self.assertEqual(updated['title'],'Getting your home ready for a grooming visit')
            self.assertEqual(updated['summary'],'Owner-written summary')
            self.assertEqual(updated['body'],'Owner-written article')
            updated=json.loads(d.execute("SELECT data FROM services WHERE slug='bath-brush'").fetchone()['data'])
            self.assertEqual(updated['description'],'Owner-written service')
            self.assertIsNone(updated['price'])
            self.assertIsNone(updated['reference'])
            self.assertEqual(d.execute('SELECT COUNT(*) FROM articles').fetchone()[0],5)
        for slug in ('choosing-a-dog-brush','introducing-your-cat-to-grooming'):
            page=self.customer.get('/care-guides/'+slug+'/').get_data(as_text=True)
            self.assertIn('<h2>',page)
            self.assertIn('Further reading',page)
        home=self.customer.get('/').get_data(as_text=True)
        self.assertIn('Tailvic<span',home)
        self.assertNotIn('<span>tailvic',home)
        self.assertIn('/careers/',home)

    def test_homepage_refresh_has_no_fabricated_profiles_or_customer_stories(self):
        page=self.customer.get('/').get_data(as_text=True)
        for text in ('A SIMPLE ENQUIRY','Gurugram Sectors 69, 70 & 71','At-home grooming is currently available in Sectors 69, 70 and 71'):
            self.assertIn(text,page)
        for text in ('class="story-card"','Aanya · Grooming stylist','Illustrative team profile','These are not customer results','Book Now','reserve an available published slot'):
            self.assertNotIn(text,page)
        team=self.customer.get('/our-groomers/').get_data(as_text=True)
        self.assertIn('We do not publish groomer profiles yet.',team)
        for name in ('Aanya','Rohan','Meera'):
            self.assertNotIn(name,team)

    def test_home_copy_and_link_only_breed_navigation(self):
        from homepage_content import PILLARS, HOME_BENEFITS, WHY_TAILVIC
        page=self.customer.get('/').get_data(as_text=True)
        self.assertNotIn('built-in method',page)
        self.assertNotIn('dict object at',page)
        self.assertNotIn('class="core-pillars"',page)
        self.assertNotIn('home-vs-salon',page)
        self.assertNotIn('class="container final-wrap"',page)
        self.assertNotIn('Book a groom',page)
        self.assertIn('Ask about grooming',page)
        self.assertNotIn('What changes when the appointment comes to you?',page)
        self.assertNotIn('Home grooming can be a good fit for many pets.',page)
        self.assertNotIn('your Gurgaon locality',page)
        self.assertEqual(len(HOME_BENEFITS),5)
        self.assertEqual(len(WHY_TAILVIC),5)
        for benefit in HOME_BENEFITS:
            self.assertLessEqual(len(benefit['title'].split()),2)
            self.assertIn('images/'+benefit['image'],page)
        for item in HOME_BENEFITS:
            self.assertIn(item['copy'],page)
        self.assertNotIn('class="breed-section"',page)
        self.assertNotIn('wellness-section',page)
        self.assertNotIn('future-section',page)
        self.assertNotIn('membership-section',page)
        self.assertIn('GROOMING ADVICE',page)
        checklist=self.customer.get('/care-guides/prepare-for-home-grooming/').get_data(as_text=True)
        self.assertIn('Your Tailvic groomer comes to your home.',checklist)
        self.assertNotIn('Before your visit',checklist)

    def test_journal_images_are_distinct_and_match_article_pages(self):
        home=self.customer.get('/').get_data(as_text=True)
        journal=home.split('GROOMING ADVICE',1)[1].split('</section>',1)[0]
        images=re.findall(r'<img[^>]+src="([^"]+)"',journal)
        self.assertEqual(len(images),3)
        self.assertEqual(len(set(images)),3)
        for slug,image in zip(('choosing-a-dog-brush','introducing-your-cat-to-grooming','prepare-for-home-grooming'),images):
            article=self.customer.get('/care-guides/'+slug+'/').get_data(as_text=True)
            self.assertIn('src="'+image+'"',article)

    def test_breed_guides_use_individual_photography(self):
        from homepage_content import BREED_VISUALS
        images=set()
        for slug,visual in BREED_VISUALS.items():
            page=self.customer.get('/care-guides/breeds/'+slug+'/').get_data(as_text=True)
            self.assertIn(visual['image'],page)
            self.assertIn(visual['alt'],page)
            with self.customer.get('/static/images/'+visual['image']) as asset:
                self.assertEqual(asset.status_code,200)
            images.add(visual['image'])
        self.assertEqual(len(images),7)

if __name__=='__main__':
    unittest.main()

