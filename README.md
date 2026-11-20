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

Vercel's native GitHub integration connects this repository to the existing
`tailvic/tailvic-demo` project. Its production branch must be `main`. A push to
that branch triggers a production build; other eligible branches can create
preview deployments. GitHub CI and Vercel run independently; Vercel's own build
also runs the full checks before publishing, so a failed check blocks that
production build. The prior deployment remains live if the build fails.

- Live domains: https://tailvic.in/ and https://www.tailvic.in/
- Vercel URL: https://tailvic-demo.vercel.app/
- Framework preset: Other (`null`)
- Root directory: repository root
- Python version: 3.11 (`.python-version`)
- Output directory: `public`
- Build command is defined in `vercel.json` and installs dependencies, runs the
  checks, then exports the site.
- No database or account secrets are required for this static build.

To connect or repair the integration, sign in to the Tailvic Vercel account,
connect the GitHub login under account Authentication, and grant the Vercel
GitHub App access to this repository. The repository owner may need to approve
that installation. In the Vercel project's Git settings, connect this repository
and select `main` as the production branch. Keep the existing project so its
custom domains continue to follow deployments.

Vercel Hobby restricts automatic deployments from private repositories to
commits authored by the Hobby project owner's connected Git identity.
Collaborator access to GitHub alone does not grant everyone Vercel deployment
rights. Team-authored production deployments require a supported Vercel plan
and permissions. See https://vercel.com/docs/deployments/troubleshoot-project-collaboration.

Local databases, session keys, Vercel sign-in tokens, virtual environments and
generated files are excluded by `.gitignore` and `.vercelignore`. Do not add
credentials from your computer or hosting account. Source content is in
`content.py`, `homepage_content.py`, `templates/` and `static/`.
