# Architecture and source map

Last reviewed: 2026-11-20.

## Production build

```text
content.py + homepage_content.py + templates/ + static/
                      |
            scripts/export_preview.py
                      |
        Flask test client + temporary seeded SQLite
                      |
               public/ (generated)
                      |
          Vercel prebuilt static deployment
                      |
                  tailvic.in
```

`scripts/export_preview.py` sets `TAILVIC_STATIC_EXPORT=1` before importing
`create_app`. It creates an isolated temporary seeded database for public content
and renders an allowlist of routes using the Flask test client. It never reads
an existing customer database from `instance/`. Generated HTML and approved
assets go into `public/`; the temporary database is discarded.

The exporter replaces booking and careers handlers with contact information,
and uses `templates/preview_login.html` / `preview_dashboard.html` for the fixed
browser roles. File names containing "preview" are internal implementation
names; the visible site has no demo notice or displayed login credentials.

Canonical URLs and CSRF meta tags are removed from exported HTML. The export
adds the `tailvic-preview` meta marker to disable server-dependent analytics and
cookie controls in `static/app.js`. It also keeps noindex robots directives.
Search indexing is therefore currently disabled; changing SEO/indexing is a
separate intentional task, not part of routine content edits.

## Source map

| Path | Responsibility |
| --- | --- |
| `app.py` | Flask application factory, public routes, local database/backend flows |
| `content.py` | Seed service menu, articles, policy and supporting content |
| `homepage_content.py` | Homepage section data and breed/story visuals |
| `templates/base.html` | Shared page shell, navigation and footer |
| `templates/home.html`, `_home_*.html` | Homepage and reusable homepage sections |
| `templates/services.html` | Services, packages and service-detail pricing explanation |
| `templates/_cards.html` | Shared service/article card macros |
| `templates/preview_login.html`, `preview_dashboard.html` | Exported account experiences |
| `static/style.css`, `home-refresh.css` | Shared styling and selected homepage design |
| `static/app.js` | Navigation, service filters and progressive enhancement |
| `static/demo-login.js`, `demo-login.css` | Fixed browser login and role-based presentation |
| `static/images/`, `static/fonts/` | Committed local images, fonts and font licence |
| `scripts/export_preview.py` | Production static export and route/form checks |
| `tests/test_app.py` | Flask/backend behaviour checks using disposable test data |
| `tests/test_preview.py` | Exported references, forms and publication-boundary checks |
| `.github/workflows/ci.yml` | Tests, build and production deployment |
| `vercel.json` | Static build/output and response headers |

## Local backend versus exported site

Running `python app.py` starts the original Flask/SQLite application. It has
registration, booking, UPI-reference, recruitment and admin operations that are
not enabled by the static export. These routes are useful source for future
work, but testing them locally does not prove the corresponding production
feature exists. UPI-reference handling is not automatic bank settlement.

To reproduce production, run the exporter and serve `public/` with a static
HTTP server. In particular, verify account and booking changes there.

`app.py` may create ignored local session-key files under `instance/`; tests
use disposable databases. Never deploy those files. Vercel receives the prebuilt
static output, not a persistent SQLite service.

## Working boundaries

Changing a source template or content seed requires rebuilding the export.
Changing an admin-editable local database does not update production. New public
routes and asset types may require exporter changes and publication checks.
Keep credentials, private routes and backend POST forms out of static output.

Secure accounts or saved bookings require a backend, persistent storage and
server-side authorization. Define that architecture and acceptance criteria
before replacing the current browser-only roles. Avoid accidental framework or
hosting changes just to modify a page.
