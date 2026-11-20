"""Check that the deployable preview includes no working forms or private data."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.forms = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.forms.append(attrs)
        if tag in ('a', 'link', 'img', 'script', 'iframe'):
            url = attrs.get('href') or attrs.get('src')
            if url:
                self.links.append(url)


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_preview.py')], cwd=ROOT, check=True, capture_output=True)
        cls.public = ROOT / 'public'

    def test_all_local_page_and_asset_references_exist(self):
        for page in self.public.rglob('*.html'):
            for link in References(page.read_text(encoding='utf-8')).links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                path = unquote(parsed.path)
                target = self.public / path.lstrip('/') if path.startswith('/') else page.parent / path
                self.assertTrue(target.is_file() or (target / 'index.html').is_file(), f'{page}: missing {link}')

    def test_only_dummy_login_form_is_published(self):
        for page in self.public.rglob('*.html'):
            parser = References(page.read_text(encoding='utf-8'))
            if page == self.public / 'account' / 'index.html':
                self.assertEqual(len(parser.forms), 1)
                self.assertIn('data-demo-login', parser.forms[0])
                self.assertEqual(parser.forms[0].get('action'), '#')
            else:
                self.assertEqual(parser.forms, [], str(page))

    def test_no_database_credentials_or_customer_pages_published(self):
        forbidden = {'.sqlite', '.db', '.py', '.xlsx', '.log'}
        for path in self.public.rglob('*'):
            if path.is_file():
                self.assertNotIn(path.suffix, forbidden, str(path))
                self.assertNotEqual(path.name, '.local-admin.txt')
        self.assertFalse((self.public / 'booking').exists())
        self.assertIn('data-demo-page="admin"', (self.public / 'admin/index.html').read_text(encoding='utf-8'))
        self.assertIn('data-demo-page="customer"', (self.public / 'account/dashboard/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
