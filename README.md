# Tailvic

Source for the selected Tailvic design currently deployed at
https://tailvic-demo.vercel.app/ in the Vercel **Tailvic** workspace,
project **tailvic-demo**.

This folder is self-contained. It includes the chosen backup design, responsive
pages, fonts and images, fixed customer/admin sign-in pages, static exporter,
Vercel configuration and tests. It does not depend on the original backup folder.

## Build and view the deployed version locally

Use Python 3.11 or newer. From this folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/export_preview.py
.\.venv\Scripts\python.exe -m http.server 5008 --bind 127.0.0.1 --directory public
```

Open http://127.0.0.1:5008/. The sign-in page is `/account/`. An interactive
390px phone preview is available at `/static/phone-preview.html`.
Stop the local server with Ctrl+C.

The static build exports 35 public routes into `public/`. Temporary seeded
SQLite is used only while rendering the pages. No database is deployed, and
no existing customer data is read. Generated output is ignored by Git.

## Current functionality

The homepage, information pages, service filters, navigation and fixed account
roles work in the browser. No registration, OTP, payments, booking submission,
pet creation or dashboard editing is enabled. Booking and application pages
offer contact options. Dashboards show empty states and the public service menu.

The fixed logins are implemented in `static/demo-login.js` using session storage.
Their values are downloadable with the public JavaScript; they are not secrets
or secure authentication. No private records should be added behind these roles.
The visible pages do not display credentials or demo labels.

The original Flask backend source is included for future development. Running
`app.py` starts that separate database-backed application; use the static build
commands above to reproduce the Vercel version.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The checks cover the Flask source and the generated public site's page/asset
references, login form restrictions and exclusion of private database files.

## Push this folder to Git

Create an empty repository on your Git provider, then run these commands from
this folder, replacing `YOUR_REPOSITORY_URL` with its clone URL:

```powershell
git init
git add .
git status
git commit -m "Add Tailvic website and Vercel static build"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

No repository, commit, remote or automatic deployment integration has been
created for you. Share the repository URL when ready to connect it to the
existing Vercel project.

## Vercel settings for the later Git integration

- Workspace: Tailvic (`tailvic`)
- Existing project: `tailvic-demo`
- Root directory: repository root
- Framework preset: Other (`null`)
- Build command: `python -m pip install -r requirements.txt && python scripts/export_preview.py`
- Output directory: `public`
- Production branch: `main`
- No database, account secrets or environment variables are needed for this build.

`vercel.json` contains the build and output settings. Preserve framework `null`
so the deployed result is the static export. After integration is connected,
pushes to the production branch can deploy production; other branches can
receive preview deployments, subject to repository and Vercel permissions.

Local databases, session keys, Vercel sign-in tokens, virtual environments and
generated files are excluded by `.gitignore` and `.vercelignore`. Do not add
credentials from your computer or hosting account. Source content is in
`content.py`, `homepage_content.py`, `templates/` and `static/`.
