"""Export seeded public pages; no database or server is published."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['TAILVIC_STATIC_EXPORT'] = '1'

from flask import render_template
from app import create_app
from content import POLICIES


def export():
    output = ROOT / 'public'
    output.mkdir(exist_ok=True)
    for old in output.rglob('*.html'):
        old.unlink()
    with tempfile.TemporaryDirectory(prefix='tailvic-export-') as scratch:
        site = create_app({'TESTING': True, 'DATABASE': str(Path(scratch) / 'seed-only.sqlite'),
                           'SECRET_KEY': 'disposable-static-build-session', 'SESSION_COOKIE_SECURE': False})

        def unavailable():
            return render_template('info.html', title='Get in touch | Tailvic',
                heading='Let’s plan a care day.', kind='contact',
                body='Online booking and applications are currently unavailable. '
                     'Please contact Tailvic by phone or WhatsApp to speak with the team.')

        for endpoint in ('book', 'careers'):
            site.view_functions[endpoint] = unavailable
        site.view_functions['account'] = lambda: render_template('preview_login.html', title='Sign in | Tailvic')
        site.view_functions['admin'] = lambda: render_template('preview_dashboard.html', title='Studio | Tailvic', demo_role='admin')
        site.add_url_rule('/account/dashboard/', 'preview_customer', lambda: render_template(
            'preview_dashboard.html', title='Your care corner | Tailvic', demo_role='customer'))
        client = site.test_client()
        sitemap = ElementTree.fromstring(client.get('/sitemap.xml').data)
        paths = {'/'}
        for node in sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            paths.add(urlsplit(node.text).path)
        paths.update('/' + name + '/' for name in POLICIES)
        paths.update(('/membership/', '/account/', '/book/', '/careers/', '/admin/'))
        paths.add('/account/dashboard/')
        for path in sorted(paths):
            response = client.get(path)
            if response.status_code != 200:
                raise RuntimeError(f'Cannot export {path}: HTTP {response.status_code}')
            html = response.get_data(as_text=True)
            html = re.sub(r'<meta name="csrf-token"[^>]*>', '', html)
            html = re.sub(r'<link rel="canonical"[^>]*>', '', html)
            html = html.replace('http://localhost/static/', '/static/')
            html = re.sub(r'<button[^>]*data-cookie-open[^>]*>.*?</button>', '', html)
            html = html.replace('</head>', '<meta name="tailvic-preview" content="true">'
                                '<meta name="robots" content="noindex,nofollow">'
                                '<link rel="stylesheet" href="/static/preview-notice.css"></head>')
            if '<form' in html.lower() and not (path=='/account/' and html.lower().count('<form')==1 and 'data-demo-login' in html):
                raise RuntimeError(f'A live form must not be published in preview: {path}')
            target = output / path.strip('/') / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding='utf-8')
    for source in (ROOT / 'static').rglob('*'):
        if source.is_file() and source.suffix.lower() in {'.css', '.js', '.json', '.webp', '.svg', '.ttf', '.woff', '.woff2', '.txt'}:
            target = output / 'static' / source.relative_to(ROOT / 'static')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in ('phone-preview.html', 'preview.html', 'review-mobile.html'):
        shutil.copy2(ROOT / 'static' / name, output / 'static' / name)
    (output / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    (output / '404.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="robots" content="noindex">'
        '<title>Page unavailable | Tailvic</title><h1>This page is unavailable.</h1>'
        '<p><a href="/">Return to Tailvic</a></p></html>', encoding='utf-8')
    settings = json.loads((ROOT / 'vercel.json').read_text(encoding='utf-8'))
    settings.pop('buildCommand', None)
    settings['outputDirectory'] = '.'
    (output / 'vercel.json').write_text(json.dumps(settings, indent=2), encoding='utf-8')
    print(f'Exported {len(paths)} public preview pages to {output}')
    return paths


if __name__ == '__main__':
    export()
