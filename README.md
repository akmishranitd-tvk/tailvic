# Tailvic

Source for the selected Tailvic design currently deployed at
https://tailvic.in/ in the Vercel **Tailvic** workspace,
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

## Repository and deployment pipeline

Repository: https://github.com/akmishranitd-tvk/tailvic

The production branch is `main`. `.github/workflows/ci.yml` runs the application
checks and static build on pushes to `main` and pull requests targeting `main`.
The workflow uses Python 3.11 and needs no deployment secrets.

GitHub Actions deploys production after successful checks on every push to
`main`, or a manual run selected on `main`. Pull requests run checks without
receiving deployment credentials or publishing production. The workflow builds
with Vercel CLI and uploads the prebuilt result to the existing project.

- Live domains: https://tailvic.in/ and https://www.tailvic.in/
- Vercel project: `tailvic/tailvic-demo`
- Framework preset: Other (`null`)
- Root directory: repository root
- Python version: 3.11 (`.python-version`)
- Output directory: `public`
- Build command is defined in `vercel.json`; failed checks stop publishing.
- No database is needed for this static site.

## Deployment credentials

The deployment step reads three encrypted GitHub repository secrets:
`VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID`. No token is committed
to source. Use a token scoped to the existing Tailvic project, and rotate it
before expiry. Store the new token in the repository's Actions secrets.
Collaborators who can change trusted workflows can use the deployment secret
to deploy to this project.

Vercel's native connector requires ownership of a repository held by a personal
GitHub account, so collaborator access alone cannot connect this repository.
This project instead uses the documented external GitHub Actions method:
https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel.
Do not enable a second deployment trigger alongside this workflow.

Local databases, session keys, Vercel sign-in tokens, virtual environments and
generated files are excluded by `.gitignore` and `.vercelignore`. Do not add
credentials from your computer or hosting account. Source content is in
`content.py`, `homepage_content.py`, `templates/` and `static/`.
