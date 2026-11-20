# Tailvic

Live website: **https://tailvic.in/**

This repository is the source for the website deployed to the Vercel workspace
`tailvic`, project `tailvic-demo`. Development handover covers the deployed web
experience, its delivery pipeline and unfinished features.

## Live links

- Website: https://tailvic.in/
- Services: https://tailvic.in/services/
- Sign in: https://tailvic.in/account/
- Customer dashboard: https://tailvic.in/account/dashboard/
- Admin dashboard: https://tailvic.in/admin/
- Mobile preview: https://tailvic.in/static/phone-preview.html
- Alternate URL: https://tailvic-demo.vercel.app/

## Current admin and user credentials

Use https://tailvic.in/account/ to sign in.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@tailvic.example` | `TailvicDemo2026!` |
| User | `customer@tailvic.example` | `TailvicDemo2026!` |

These fixed accounts are implemented in public browser JavaScript. They provide
role-specific presentation, not secure authentication. Dashboards contain empty
states and public service information. No real private records or payments are
stored behind them. These are site test identities, not hosting/GitHub credentials.
The visible website does not display these login details or demo banners.

## Start here: colleague or coding agent

1. Read [AGENTS.md](AGENTS.md) and [the handover](docs/handover.md).
2. Read [unfinished tasks](docs/tasks.md) before assuming a feature already works.
3. Use [architecture](docs/architecture.md) to find the relevant source.
4. Follow [operations](docs/operations.md) to deploy and verify on `tailvic.in`.

Claude Code has [CLAUDE.md](CLAUDE.md) importing the shared agent instructions.
Substantial feature requests can use [the change template](specs/change-template.md).
The [current site baseline](specs/current-site.md) records existing behaviour.

## How changes reach the website

Pushes to `main` automatically run `.github/workflows/ci.yml`: install dependencies,
run the application/site checks, export the public site, build with Vercel CLI,
and deploy the prebuilt result to the existing production project. The successful
production deployment updates `tailvic.in`. Pull requests run validation only;
automatic PR preview deployments are not configured.

The deployed site consists of static HTML, CSS, JavaScript, images and fonts.
Python/Flask/Jinja render those files during the build. No persistent database
or application server is deployed. Do not confuse backend code in the repository
with functionality available on the website.

Follow the exact commit's run at
https://github.com/akmishranitd-tvk/tailvic/actions, then check the changed page and
requested interactions on the live domain. A successful push alone is not proof
that a change is deployed or correct.

## Deployment access

GitHub Actions uses encrypted repository secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`
and `VERCEL_PROJECT_ID`. Hosting tokens, account passwords and private data must
not be added to this README or committed anywhere. The owner confirmed a
project-scoped deployment token with a 90-day expiry; check its actual expiry in
Vercel and rotate it before expiry. See the operations guide.

The pipeline uses Python 3.11, Node.js 24, `uv`, and Vercel CLI 66.2.0. Build
settings live in `vercel.json`. Keep the existing Vercel project and domain
configuration for routine changes. Generated output, databases and credentials
are ignored by Git.
