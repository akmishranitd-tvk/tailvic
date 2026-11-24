"""Tailvic: Flask, SQLite, server-rendered public pages, first-party bookings and analytics."""
import argparse
import functools
import hashlib
import json
import io
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse

from flask import Flask, abort, g, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from content import SERVICES, ARTICLES, BREEDS, FAQS, POLICIES, SIZE_GUIDES, COPY_BASELINES
from homepage_content import BREED_VISUALS, PILLARS, HOME_BENEFITS, WHY_TAILVIC

ROOT = Path(__file__).parent
IST = timezone(timedelta(hours=5, minutes=30))

def create_app(test_config=None):
    app = Flask(__name__)
    instance = ROOT / 'instance'
    instance.mkdir(exist_ok=True)
    secret_file = instance / 'session.key'
    if not secret_file.exists():
        secret_file.write_text(secrets.token_hex(32))
    app.config.update(SECRET_KEY=os.environ.get('TAILVIC_SECRET', secret_file.read_text()), DATABASE=str(instance / 'tailvic.sqlite'), MAX_CONTENT_LENGTH=64*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('TAILVIC_HTTPS')=='1', PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    if test_config:
        app.config.update(test_config)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=15, isolation_level=None)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        if 'db' in g:
            g.db.close()

    def init_db():
        db().executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer');
        CREATE TABLE IF NOT EXISTS services(slug TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS articles(slug TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS slots(id INTEGER PRIMARY KEY, starts TEXT NOT NULL UNIQUE, ends TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS bookings(id TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, pet_name TEXT NOT NULL, species TEXT NOT NULL, size TEXT NOT NULL, coat TEXT NOT NULL, service TEXT NOT NULL, address TEXT NOT NULL, pin TEXT NOT NULL, notes TEXT NOT NULL, preferred TEXT NOT NULL, slot_id INTEGER REFERENCES slots(id), status TEXT NOT NULL, base INTEGER, travel INTEGER, tax INTEGER, total INTEGER, quote_accepted INTEGER NOT NULL DEFAULT 0, payment TEXT NOT NULL DEFAULT 'unpaid', utr TEXT NOT NULL DEFAULT '', reminder INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS occupied_slot ON bookings(slot_id) WHERE slot_id IS NOT NULL AND status NOT IN ('cancelled','declined');
        CREATE TABLE IF NOT EXISTS pets(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),name TEXT NOT NULL,species TEXT NOT NULL,breed TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, event TEXT NOT NULL, path TEXT NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS limits(key TEXT PRIMARY KEY,count INTEGER NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor INTEGER,action TEXT NOT NULL,reference TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS applications(id TEXT PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL,phone TEXT NOT NULL,city TEXT NOT NULL,experience TEXT NOT NULL,species TEXT NOT NULL,availability TEXT NOT NULL,qualification TEXT NOT NULL,portfolio TEXT NOT NULL,message TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'new',created TEXT NOT NULL);
        ''')
        for s in SERVICES:
            db().execute('INSERT OR IGNORE INTO services VALUES (?,?)',(s['slug'],json.dumps(s)))
        for a in ARTICLES:
            db().execute('INSERT OR IGNORE INTO articles VALUES (?,?)',(a['slug'],json.dumps(a)))
        for table,defaults in (('services',SERVICES),('articles',ARTICLES)):
            for item in defaults:
                baseline=COPY_BASELINES.get(table,{}).get(item['slug'],{})
                if not baseline:
                    continue
                current=json.loads(db().execute(f'SELECT data FROM {table} WHERE slug=?',(item['slug'],)).fetchone()['data'])
                changed=False
                for key,old in baseline.items():
                    if current.get(key)==old:
                        current[key]=item[key]
                        changed=True
                if changed:
                    db().execute(f'UPDATE {table} SET data=? WHERE slug=?',(json.dumps(current),item['slug']))
        for key,value in {'upi':'7845475769@upi','travel_note':'Travel and applicable taxes are confirmed in your complete quote.','coverage':'Gurugram · Sectors 69, 70 and 71'}.items():
            db().execute('INSERT OR IGNORE INTO settings VALUES (?,?)',(key,value))
    with app.app_context():
        init_db()
    app.init_db = init_db
    app.get_db = db

    def now():
        return datetime.now(IST).isoformat(timespec='seconds')

    def rows(table):
        return [json.loads(r['data']) for r in db().execute(f'SELECT data FROM {table} ORDER BY rowid')]

    def setting(key):
        row=db().execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return row['value'] if row else ''

    def event(name,path='/'):
        db().execute('INSERT INTO events(event,path,created) VALUES (?,?,?)',(name,path,now()))

    def audit(action,reference):
        db().execute('INSERT INTO audit(actor,action,reference,created) VALUES (?,?,?,?)',(session.get('uid'),action,str(reference),now()))

    def limited(prefix,maximum,seconds=900):
        key=hashlib.sha256(f'{prefix}:{request.remote_addr}'.encode()).hexdigest()
        stamp=int(time.time())
        db().execute('INSERT INTO limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN expires<? THEN 1 ELSE count+1 END, expires=CASE WHEN expires<? THEN excluded.expires ELSE expires END',(key,stamp+seconds,stamp,stamp))
        if db().execute('SELECT count FROM limits WHERE key=?',(key,)).fetchone()['count']>maximum:
            abort(429,description='Too many attempts. Please try again later.')

    def user():
        return db().execute('SELECT id,name,email,phone,role FROM users WHERE id=?',(session.get('uid'),)).fetchone()

    def admin_required(fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            u=user()
            if not u:
                return redirect('/account?next=admin')
            if u['role']!='admin':
                abort(403)
            return fn(*args,**kwargs)
        return wrapped

    def owned_booking(bid):
        b=db().execute('SELECT b.*,s.starts FROM bookings b LEFT JOIN slots s ON b.slot_id=s.id WHERE b.id=?',(bid,)).fetchone()
        u=user()
        if not b or not ((u and (u['role']=='admin' or b['user_id']==u['id'])) or bid in session.get('guest_bookings',[])):
            abort(404)
        return b

    @app.before_request
    def protect():
        if 'csrf' not in session:
            session['csrf']=secrets.token_urlsafe(32)
        if request.method=='POST':
            token=request.headers.get('X-CSRF-Token') or request.form.get('csrf','')
            if not secrets.compare_digest(str(token),session['csrf']):
                abort(400,description='Your session expired. Refresh and try again.')
            if request.headers.get('Sec-Fetch-Site')=='cross-site':
                abort(403)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        # The local phone preview embeds Tailvic routes on the same origin.
        # External sites remain unable to frame any Tailvic page.
        response.headers['X-Frame-Options']='SAMEORIGIN'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        ancestor="'self'"
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors "+ancestor+"; base-uri 'self'"
        if request.path.startswith(('/account','/admin','/booking','/api','/careers')):
            response.headers['Cache-Control']='no-store'
        return response

    @app.context_processor
    def context():
        return dict(current_user=user(),csrf=session.get('csrf'),services=rows('services'),articles=rows('articles'),faqs=FAQS,breeds=BREEDS,year=datetime.now(IST).year,coverage=setting('coverage'),breed_visuals=BREED_VISUALS,pillars=PILLARS,home_benefits=HOME_BENEFITS,why_tailvic=WHY_TAILVIC)

    @app.template_filter('money')
    def money(paise):
        return 'Quote on request' if paise is None else '₹'+f'{paise/100:,.2f}'.removesuffix('.00')

    @app.template_filter('datefmt')
    def datefmt(value):
        return datetime.fromisoformat(value).strftime('%d %b, %I:%M %p')+' IST' if value else 'Preferred time requested'

    @app.route('/')
    def home():
        return render_template('home.html',title='At-home dog & cat grooming in Gurugram | Tailvic',description='Warm, thoughtful dog and cat grooming at home in Gurugram Sectors 69, 70 and 71. Ask Tailvic about a visit.')

    @app.route('/services/')
    @app.route('/packages/')
    @app.route('/services/<slug>/')
    def service_page(slug=None):
        ss=rows('services')
        species='dog' if slug=='dog-grooming' else 'cat' if slug=='cat-grooming' else None
        chosen=next((s for s in ss if s['slug']==slug),None)
        if slug and not chosen and not species:
            abort(404)
        return render_template('services.html',title=(chosen['name'] if chosen else ('Cat grooming' if species=='cat' else 'Dog grooming' if species else 'Grooming & pricing'))+' in Gurgaon | Tailvic',chosen=chosen,species=species)

    @app.route('/care-guides/')
    @app.route('/care-guides/<slug>/')
    def guides(slug=None):
        article=next((a for a in rows('articles') if a['slug']==slug),None)
        if slug and not article:
            abort(404)
        return render_template('guides.html',title=(article['title'] if article else 'Practical advice for pet parents')+' | Tailvic',article=article)

    @app.route('/careers/',methods=['GET','POST'])
    def careers():
        error=None
        if request.method=='POST':
            limited('applications',8,3600)
            f={key:request.form.get(key,'').strip() for key in ('name','email','phone','city','experience','species','availability','qualification','portfolio','message')}
            if request.form.get('website'):
                abort(400,description='Please use the application form without automated submissions.')
            limits={'name':100,'email':200,'phone':25,'city':100,'experience':10,'species':10,'availability':200,'qualification':1000,'portfolio':500,'message':3000}
            if any(len(value)>limits[key] for key,value in f.items()):
                error='Please keep your answers within the field limits.'
            elif not f['name'] or not f['city'] or not f['availability'] or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',f['email']) or not 10<=len(re.sub(r'\D','',f['phone']))<=15 or f['experience'] not in ('trainee','under-1','1-3','3-5','5-plus') or f['species'] not in ('dog','cat','both','learning') or not request.form.get('consent'):
                error='Complete your contact details, experience, species, availability, and application consent.'
            elif f['portfolio'] and (urlparse(f['portfolio']).scheme not in ('http','https') or not urlparse(f['portfolio']).netloc):
                error='Use a complete http:// or https:// link for your portfolio or CV.'
            else:
                reference='TV-J-'+secrets.token_hex(5).upper()
                db().execute('INSERT INTO applications(id,name,email,phone,city,experience,species,availability,qualification,portfolio,message,created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(reference,*(f[k] for k in ('name','email','phone','city','experience','species','availability','qualification','portfolio','message')),now()))
                audit('application_received',reference)
                session['application_received']=reference
                return redirect('/careers/')
        submitted=session.pop('application_received',None)
        return render_template('careers.html',title='Grooming careers in Gurgaon | Tailvic',error=error,submitted=submitted,form=request.form if request.method=='POST' else {})

    @app.route('/care-guides/breeds/<slug>/')
    def breed(slug):
        b=next((b for b in BREEDS if b[0]==slug),None)
        if not b:
            abort(404)
        visual=BREED_VISUALS[slug]
        article=dict(title=b[1]+' coat care',category='Coat & breed guides',minutes=3,image=visual['image'],image_alt=visual['alt'],summary=b[2],body=b[2]+'\nCoat type, age, lifestyle, condition, and handling comfort all shape a grooming plan. Tell our team about your individual pet rather than choosing by breed name alone.\nAsk which brushing tools suit your pet, what your chosen service includes, and how much time to allow. Heavy matting or unusual skin and ear concerns need individual assessment, with veterinary input where appropriate.\nWe agree a quote and estimated duration before confirming. Full grooming is not a 30-minute service. For cat care, request a cat-experienced groomer. This guide is general grooming information, not clinical advice.')
        return render_template('guides.html',title=article['title']+' | Tailvic',article=article)

    @app.route('/<page>/')
    def information(page):
        if page in POLICIES:
            title,body=POLICIES[page]
            return render_template('info.html',title=title+' | Tailvic',heading=title,body=body,kind=page)
        data={
          'our-groomers':('The people behind the care.','We do not publish groomer profiles yet. The Tailvic team will confirm who is available and discuss relevant experience before a visit is agreed.'),
          'care-standards':('Thoughtful care. Clear standards.','Our proposed care protocol starts with a suitability conversation, clean equipment, an agreed service, and permission before any change. We pause or stop when continuing is unsuitable.\nWe bring professional grooming tools and appropriate products. Please provide water, electricity, a bathing area where required, and a clean towel. We explain setup, handling, and cleanup before the visit.\nStaff certification and verification claims will be published only after evidence is checked. Ask the team about the assigned groomer before confirming.'),
          'about':('A good care day starts at home.','Tailvic is a Gurgaon pet-care startup built around a simple idea: everyday care should feel easier for pets and their people.\nWe start with at-home grooming and a human booking team. Our longer-term ambition is a connected home-based wellness platform, with new services introduced as qualified teams and care processes become ready.'),
          'areas':('Hello, Gurugram.','At-home grooming is currently available in Sectors 69, 70 and 71. Message the team with your address to check coverage and visit availability. Travel and applicable taxes are confirmed before an appointment is agreed.'),
          'wellness':('Little reminders. A little peace of mind.','Ask about reminder support based on the dates your veterinarian provides. We do not create a universal vaccination schedule or administer vaccines as part of grooming.\nVet consultations, vaccination services, nutrition, walking, daycare, training, and boarding are planned. You can register interest without committing to a booking.'),
          'contact':('A real conversation starts here.','Call +91 74857 84578, email tailvic@gmail.com, or message Tailvic on WhatsApp. Appointment requests are welcome 24/7.\nInstagram: @tailvic. For a service concern, include your booking reference so the team can help.'),
          'faqs':('Good questions. Clear answers.','Everything you need to plan a care day.'),
          'membership':('A routine worth coming back to.','Tailvic Care Routine is planned: three grooming visits, easier rebooking, and optional reminders. Proposed validity is six months for one named pet, with manual renewal.\nPricing, capacity, and full terms are being tested. Enrollment and payment are not open. Register interest for an update.'),
        }
        if page not in data:
            abort(404)
        heading,body=data[page]
        return render_template('info.html',title=heading+' | Tailvic',heading=heading,body=body,kind=page)

    @app.route('/account/',methods=['GET','POST'])
    def account():
        error=None
        if request.method=='POST':
            limited('auth',25)
            action=request.form.get('action')
            email=request.form.get('email','').strip().lower()
            password=request.form.get('password','')
            if action=='register':
                name=request.form.get('name','').strip()
                phone=re.sub(r'\D','',request.form.get('phone',''))
                if not 2<=len(name)<=100 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>200 or not 10<=len(phone)<=15 or not 10<=len(password)<=128:
                    error='Enter a name, valid email and phone, and a password of 10–128 characters.'
                else:
                    try:
                        cur=db().execute('INSERT INTO users(name,email,phone,password) VALUES (?,?,?,?)',(name,email,phone,generate_password_hash(password)))
                        session['uid']=cur.lastrowid
                    except sqlite3.IntegrityError:
                        error='An account already uses this email. Please sign in.'
            else:
                u=db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if not u or not check_password_hash(u['password'],password):
                    error='Email or password is incorrect.'
                else:
                    session['uid']=u['id']
            if not error:
                session.permanent=True
                session['csrf']=secrets.token_urlsafe(32)
                for bid in session.get('guest_bookings',[]):
                    db().execute('UPDATE bookings SET user_id=? WHERE id=? AND user_id IS NULL',(session['uid'],bid))
                session.pop('guest_bookings',None)
                return redirect('/admin/' if user()['role']=='admin' else '/account/')
        u=user()
        bookings=db().execute('SELECT b.*,s.starts FROM bookings b LEFT JOIN slots s ON b.slot_id=s.id WHERE user_id=? ORDER BY created DESC',(u['id'],)).fetchall() if u else []
        pets=db().execute('SELECT * FROM pets WHERE user_id=?',(u['id'],)).fetchall() if u else []
        return render_template('account.html',title='Your care corner | Tailvic',error=error,bookings=bookings,pets=pets)

    @app.post('/logout/')
    def logout():
        session.clear()
        return redirect('/')

    @app.post('/account/pets/')
    def pets():
        u=user()
        if not u:
            abort(401)
        name=request.form.get('name','').strip()
        species=request.form.get('species')
        breed=request.form.get('breed','').strip()
        if not 1<=len(name)<=80 or species not in ('dog','cat') or len(breed)>100:
            abort(400)
        db().execute('INSERT INTO pets(user_id,name,species,breed) VALUES (?,?,?,?)',(u['id'],name,species,breed))
        return redirect('/account/')

    def available(date=None):
        sql="SELECT s.* FROM slots s WHERE active=1 AND starts>? AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.slot_id=s.id AND b.status NOT IN ('cancelled','declined'))"
        args=[now()]
        if date:
            sql+=' AND substr(starts,1,10)=?'
            args.append(date)
        return [dict(s) for s in db().execute(sql+' ORDER BY starts',args)]

    @app.get('/api/slots/')
    def slots_api():
        return jsonify(available(request.args.get('date')))

    @app.route('/book/',methods=['GET','POST'])
    def book():
        error=None
        if request.method=='POST':
            limited('booking',20,3600)
            f={k:request.form.get(k,'').strip() for k in ('name','email','phone','pet_name','species','size','coat','service','address','pin','notes','preferred')}
            svc=next((s for s in rows('services') if s['slug']==f['service']),None)
            if any(not f[k] for k in ('name','email','phone','pet_name','address','pin')) or any(len(v)>1500 for v in f.values()) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',f['email']) or not re.fullmatch(r'\d{6}',f['pin']) or not 10<=len(re.sub(r'\D','',f['phone']))<=15 or not svc or f['species'] not in ('dog','cat') or f['size'] not in ('small','medium','large','giant') or f['coat'] not in ('short','long','double','curly') or not request.form.get('consent'):
                error='Please complete the required details, valid contact information, and booking consent.'
            elif svc['species'] not in ('both',f['species']):
                error='Please choose a service suited to your dog or cat.'
            elif f['size'] not in {option['value'] for option in SIZE_GUIDES[f['species']]}:
                error='Please choose a size category available for your dog or cat.'
            else:
                slotid=request.form.get('slot_id') if request.form.get('mode')=='slot' else None
                if request.form.get('mode')=='slot' and not slotid:
                    error='Choose a published slot or switch to a preferred-time request.'
                elif not slotid and not f['preferred']:
                    error='Tell us your preferred date and time.'
                elif not slotid:
                    try:
                        preferred=datetime.fromisoformat(f['preferred']).replace(tzinfo=IST)
                        if preferred<=datetime.now(IST) or preferred>datetime.now(IST)+timedelta(days=90):
                            raise ValueError()
                    except ValueError:
                        error='Choose a future preferred time within the next 90 days.'
                if not error:
                    bid='TV-'+secrets.token_hex(5).upper()
                    try:
                        db().execute('BEGIN IMMEDIATE')
                        if slotid and not any(str(s['id'])==slotid for s in available()):
                            raise ValueError('That slot was just reserved. Choose another time or request an appointment.')
                        u=user()
                        db().execute('INSERT INTO bookings(id,user_id,name,email,phone,pet_name,species,size,coat,service,address,pin,notes,preferred,slot_id,status,base,reminder,created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(bid,u['id'] if u else None,f['name'],f['email'],f['phone'],f['pet_name'],f['species'],f['size'],f['coat'],f['service'],f['address'],f['pin'],f['notes'],f['preferred'],slotid,'reserved' if slotid else 'requested',svc['price'],int(bool(request.form.get('reminder'))),now()))
                        event('enquiry_received','/book/')
                        audit('booking_created',bid)
                        db().execute('COMMIT')
                        session['guest_bookings']=(session.get('guest_bookings',[])+[bid])[-30:]
                        return redirect('/booking/'+bid+'/')
                    except (sqlite3.IntegrityError,ValueError) as exc:
                        db().execute('ROLLBACK')
                        error=str(exc) if isinstance(exc,ValueError) else 'That slot was just reserved. Please choose another.'
        all_services=rows('services')
        selected=request.form.get('service') or request.args.get('service','')
        selected_service=next((s for s in all_services if s['slug']==selected),None)
        pet_species=request.form.get('species') if request.form.get('species') in SIZE_GUIDES else ('cat' if selected_service and selected_service['species']=='cat' else 'dog')
        book_services=[s for s in all_services if s['species'] in ('both',pet_species)]
        if not any(s['slug']==selected for s in book_services):
            selected=book_services[0]['slug']
        return render_template('book.html',title='Plan a care day | Tailvic',slots=available(),error=error,selected=selected,form=request.form,pet_species=pet_species,size_guides=SIZE_GUIDES,book_services=book_services)

    @app.route('/booking/<bid>/',methods=['GET','POST'])
    def booking(bid):
        b=owned_booking(bid)
        error=None
        if request.method=='POST':
            action=request.form.get('action')
            if action=='accept' and b['status']=='quoted' and b['total'] is not None:
                db().execute("UPDATE bookings SET status='confirmed',quote_accepted=1 WHERE id=?",(bid,))
                event('booking_confirmed','/booking/')
                audit('quote_accepted',bid)
            elif action=='payment' and b['quote_accepted'] and b['status'] in ('confirmed','completed') and b['payment']!='verified':
                utr=request.form.get('utr','').strip()
                if not re.fullmatch(r'[A-Za-z0-9]{8,40}',utr):
                    error='Enter an 8–40 character transaction reference.'
                else:
                    db().execute("UPDATE bookings SET payment='awaiting_verification',utr=? WHERE id=?",(utr,bid))
                    audit('payment_submitted',bid)
            elif action=='cancel' and b['status'] not in ('cancelled','completed','declined'):
                db().execute("UPDATE bookings SET status='cancelled' WHERE id=?",(bid,))
                audit('customer_cancelled',bid)
            else:
                abort(400)
            if not error:
                return redirect('/booking/'+bid+'/')
        b=owned_booking(bid)
        upi='upi://pay?'+urlencode(dict(pa=setting('upi'),pn='Tailvic',am=f'{b["total"]/100:.2f}',cu='INR',tn=bid)) if b['total'] is not None and b['quote_accepted'] else None
        return render_template('booking.html',title='Your appointment | Tailvic',booking=b,error=error,upi=upi,upi_id=setting('upi'))

    @app.get('/booking/<bid>/payment-qr.svg')
    def payment_qr(bid):
        b=owned_booking(bid)
        if not b['quote_accepted'] or b['total'] is None or b['status'] not in ('confirmed','completed'):
            abort(403)
        import qrcode
        from qrcode.image.svg import SvgPathImage
        payload='upi://pay?'+urlencode(dict(pa=setting('upi'),pn='Tailvic',am=f'{b["total"]/100:.2f}',cu='INR',tn=bid))
        image=qrcode.make(payload,image_factory=SvgPathImage,box_size=6,border=4)
        output=io.BytesIO()
        image.save(output)
        return app.response_class(output.getvalue(),mimetype='image/svg+xml')

    @app.post('/api/events/')
    def analytics():
        limited('events',240,3600)
        d=request.get_json(silent=True) or {}
        if request.cookies.get('tailvic_analytics')!='yes':
            return '',204
        if d.get('event') not in ('page_view','whatsapp_click','phone_click','booking_start'):
            abort(400)
        path=d.get('path','/')
        if not isinstance(path,str) or len(path)>100 or not re.fullmatch(r'/[a-z0-9/\-]*',path) or path.startswith(('/booking/','/admin/','/account/')):
            path='/'
        event(d['event'],path)
        return '',204

    @app.route('/admin/',methods=['GET','POST'])
    @admin_required
    def admin():
        error=None
        if request.method=='POST':
            action=request.form.get('action')
            try:
                if action=='service':
                    slug=request.form['slug']
                    s=next((s for s in rows('services') if s['slug']==slug),None)
                    if not s:
                        raise ValueError('Unknown service.')
                    name=request.form['name'].strip()
                    price=request.form['price'].strip()
                    if not name or len(name)>100 or (price and not re.fullmatch(r'\d{1,6}(\.\d{1,2})?',price)):
                        raise ValueError('Enter a valid service name and price.')
                    s.update(name=name,description=request.form['description'][:1000],duration=request.form['duration'][:100],includes=[x.strip() for x in request.form['includes'].splitlines() if x.strip()][:12],price=round(float(price)*100) if price else None)
                    s['reference']=None
                    db().execute('UPDATE services SET data=? WHERE slug=?',(json.dumps(s),slug))
                    audit('service_edited',slug)
                elif action=='application_status':
                    reference=request.form.get('application_id','')
                    status=request.form.get('status','')
                    if status not in ('new','reviewing','contacted','shortlisted','closed') or not db().execute('SELECT id FROM applications WHERE id=?',(reference,)).fetchone():
                        raise ValueError('Choose an existing application and a valid review status.')
                    db().execute('UPDATE applications SET status=? WHERE id=?',(status,reference))
                    audit('application_'+status,reference)
                elif action=='article':
                    slug=request.form['slug']
                    a=next((a for a in rows('articles') if a['slug']==slug),None)
                    if not a:
                        raise ValueError('Unknown article.')
                    for key in ('title','summary','body'):
                        a[key]=request.form[key].strip()[:12000]
                        if not a[key]:
                            raise ValueError('Complete all article fields.')
                    db().execute('UPDATE articles SET data=? WHERE slug=?',(json.dumps(a),slug))
                    audit('article_edited',slug)
                elif action=='slot':
                    start=datetime.fromisoformat(request.form['starts']).replace(tzinfo=IST)
                    end=start+timedelta(minutes=120)
                    if start<=datetime.now(IST) or start>datetime.now(IST)+timedelta(days=90):
                        raise ValueError('Publish a future slot within 90 days.')
                    db().execute('BEGIN IMMEDIATE')
                    if db().execute('SELECT id FROM slots WHERE active=1 AND starts<? AND ends>?',(end.isoformat(timespec='seconds'),start.isoformat(timespec='seconds'))).fetchone():
                        raise ValueError('This overlaps an existing two-hour appointment window.')
                    db().execute('INSERT INTO slots(starts,ends) VALUES (?,?)',(start.isoformat(timespec='seconds'),end.isoformat(timespec='seconds')))
                    audit('slot_published',start.isoformat())
                    db().execute('COMMIT')
                elif action=='close_slot':
                    sid=request.form['slot_id']
                    if db().execute("SELECT id FROM bookings WHERE slot_id=? AND status NOT IN ('cancelled','declined')",(sid,)).fetchone():
                        raise ValueError('Resolve the associated booking before closing this slot.')
                    db().execute('UPDATE slots SET active=0 WHERE id=?',(sid,))
                    audit('slot_closed',sid)
                elif action=='quote':
                    bid=request.form['bid']
                    b=db().execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
                    if not b or b['status'] not in ('requested','reserved','quoted'):
                        raise ValueError('Only pending appointments can be quoted.')
                    amounts=[]
                    for key in ('base','travel','tax'):
                        raw=request.form[key]
                        if not re.fullmatch(r'\d{1,6}(\.\d{1,2})?',raw):
                            raise ValueError('Enter a valid non-negative amount for every quote line.')
                        amounts.append(round(float(raw)*100))
                    if sum(amounts)<=0:
                        raise ValueError('Total must be positive.')
                    db().execute('BEGIN IMMEDIATE')
                    if b['slot_id'] is None:
                        start=datetime.fromisoformat(request.form.get('confirmed_starts','')).replace(tzinfo=IST)
                        end=start+timedelta(minutes=120)
                        if start<=datetime.now(IST):
                            raise ValueError('Confirm a future appointment time with this quote.')
                        matching=db().execute('SELECT id FROM slots WHERE starts=? AND active=1',(start.isoformat(timespec='seconds'),)).fetchone()
                        if matching:
                            sid=matching['id']
                            if db().execute("SELECT id FROM bookings WHERE slot_id=? AND status NOT IN ('cancelled','declined')",(sid,)).fetchone():
                                raise ValueError('The proposed appointment time is already reserved.')
                        else:
                            if db().execute('SELECT id FROM slots WHERE active=1 AND starts<? AND ends>?',(end.isoformat(timespec='seconds'),start.isoformat(timespec='seconds'))).fetchone():
                                raise ValueError('The proposed time overlaps an existing appointment window.')
                            sid=db().execute('INSERT INTO slots(starts,ends) VALUES (?,?)',(start.isoformat(timespec='seconds'),end.isoformat(timespec='seconds'))).lastrowid
                        db().execute('UPDATE bookings SET slot_id=? WHERE id=?',(sid,bid))
                    db().execute("UPDATE bookings SET base=?,travel=?,tax=?,total=?,quote_accepted=0,status='quoted' WHERE id=?",(*amounts,sum(amounts),bid))
                    audit('quote_sent',bid)
                    event('quote_sent','/admin/')
                    db().execute('COMMIT')
                elif action=='booking_status':
                    bid=request.form['bid']
                    status=request.form['status']
                    b=db().execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
                    allowed={'requested':{'declined','cancelled'},'reserved':{'declined','cancelled'},'quoted':{'declined','cancelled'},'confirmed':{'completed','cancelled'},'completed':set(),'cancelled':set(),'declined':set()}
                    if not b or status not in allowed.get(b['status'],set()):
                        raise ValueError('That status transition is not available.')
                    db().execute('UPDATE bookings SET status=? WHERE id=?',(status,bid))
                    event('service_completed' if status=='completed' else 'booking_cancelled','/admin/')
                    audit('booking_'+status,bid)
                elif action=='verify_payment':
                    b=db().execute('SELECT * FROM bookings WHERE id=?',(request.form['bid'],)).fetchone()
                    if not b or b['payment']!='awaiting_verification' or b['status'] not in ('confirmed','completed'):
                        raise ValueError('No eligible payment awaits verification.')
                    db().execute("UPDATE bookings SET payment='verified' WHERE id=?",(b['id'],))
                    audit('payment_verified',b['id'])
                else:
                    raise ValueError('Unknown action.')
                return redirect('/admin/#'+request.form.get('section','overview'))
            except (ValueError,KeyError,sqlite3.IntegrityError) as exc:
                if db().in_transaction:
                    db().execute('ROLLBACK')
                error=str(exc)
        bookings=db().execute('SELECT b.*,s.starts FROM bookings b LEFT JOIN slots s ON b.slot_id=s.id ORDER BY b.created DESC').fetchall()
        metrics={r['event']:r['n'] for r in db().execute('SELECT event,COUNT(*) n FROM events GROUP BY event')}
        totals=dict(db().execute("SELECT COUNT(*) appointments,COALESCE(SUM(CASE WHEN payment='verified' THEN total ELSE 0 END),0) collected FROM bookings").fetchone())
        return render_template('admin.html',title='Tailvic studio | Admin',error=error,bookings=bookings,metrics=metrics,totals=totals,all_slots=db().execute('SELECT * FROM slots WHERE active=1 AND starts>? ORDER BY starts',(now(),)).fetchall(),applications=db().execute('SELECT * FROM applications ORDER BY created DESC,id DESC').fetchall())

    @app.get('/robots.txt')
    def robots():
        return app.response_class('User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /account/\nDisallow: /book/\nDisallow: /booking/\nDisallow: /api/\n',mimetype='text/plain')

    @app.get('/sitemap.xml')
    def sitemap():
        paths=['/','/services/','/services/dog-grooming/','/services/cat-grooming/','/packages/','/our-groomers/','/care-standards/','/areas/','/about/','/wellness/','/contact/','/faqs/','/care-guides/','/careers/']+['/care-guides/'+a['slug']+'/' for a in rows('articles')]+['/care-guides/breeds/'+b[0]+'/' for b in BREEDS]
        from xml.sax.saxutils import escape
        base=os.environ.get('TAILVIC_PUBLIC_URL',request.url_root.rstrip('/'))
        return app.response_class('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(base+p)+'</loc></url>' for p in paths)+'</urlset>',mimetype='application/xml')

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(429)
    def error_page(error):
        return render_template('error.html',title='Let’s find your way | Tailvic',code=error.code,message=error.description),error.code
    return app

app=None if os.environ.get('TAILVIC_STATIC_EXPORT')=='1' else create_app()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=5000)
    parser.add_argument('--create-admin',action='store_true')
    args=parser.parse_args()
    if args.create_admin:
        with app.app_context():
            existing=app.get_db().execute("SELECT id FROM users WHERE role='admin'").fetchone()
            if not existing:
                password=secrets.token_urlsafe(18)
                app.get_db().execute('INSERT INTO users(name,email,phone,password,role) VALUES (?,?,?,?,?)',('Tailvic owner','admin@tailvic.local','7485784578',generate_password_hash(password),'admin'))
                (ROOT/'.local-admin.txt').write_text('Local Tailvic admin\nURL: http://127.0.0.1:5000/account/\nEmail: admin@tailvic.local\nPassword: '+password+'\nDo not publish or commit this file.\n')
                print('Admin created. Credentials saved to .local-admin.txt (ignored by Git).')
            else:
                print('Admin already exists; credentials unchanged.')
    else:
        app.run(host='127.0.0.1',port=args.port,debug=False)
