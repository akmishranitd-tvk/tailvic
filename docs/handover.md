# Tailvic development handover

Last reviewed: 2026-11-20. Intended for the next four weeks of development by
the owner's colleague and a coding agent, including Claude Code.

## First session

1. Read `AGENTS.md` and `README.md`, then `docs/architecture.md`.
2. Install dependencies, run the checks and open the generated static site.
3. Read `docs/operations.md` before publishing. A push to `main` changes the
   live site automatically after successful checks.
4. Get the next requested change and its acceptance criteria from the owner.
   A four-week feature roadmap has not yet been approved.

Suggested opening prompt for any coding agent:

> Read AGENTS.md, docs/handover.md and the linked architecture/operations notes.
> Explain the current production behaviour and limitations before implementing
> my requested change. Use the current repository as source. When I request
> deployment, push through the documented main-branch pipeline, watch the run,
> and verify the requested result on tailvic.in. Report what was checked.

## Current production baseline

- Repository: https://github.com/akmishranitd-tvk/tailvic (private).
- Live: https://tailvic.in/ and https://www.tailvic.in/.
- Alternate: https://tailvic-demo.vercel.app/.
- Vercel workspace/project: `tailvic/tailvic-demo`.
- Selected design originated from a backup; all necessary source is now in this
  repository. No external backup folder is needed to build or develop it.
- Python 3.11, Flask/Jinja for rendering, vanilla JavaScript/CSS and local assets.
- Static export of 35 public routes at handover. No live database or application
  server is required by the deployed site.

The pre-handover production baseline is commit `4eb5764`, which passed all 25
checks and deployed through GitHub Actions. Its successful run is
https://github.com/akmishranitd-tvk/tailvic/actions/runs/44699449267.
Future commits and Actions runs supersede this dated baseline.

## Works today

Public content pages, responsive navigation, service filters, care guides,
contact links, and fixed customer/admin browser sign-in flows. The account page
is `/account/`; customer landing is `/account/dashboard/`; admin is `/admin/`.
Dashboards use empty states and the public service menu. Browser role values
are stored in session storage, so account testing must include sign-out or a
fresh browser session. The fixed test identities are defined in
`static/demo-login.js`; they are public application code, not private secrets.

## Not enabled in production

New-user registration, email OTP, secure server-side authentication, persistent
users/pets/appointments, booking submissions, payment processing, dashboard
editing and application submissions. Booking and careers pages direct visitors
to contact the team. Do not infer production support from routes in `app.py`:
the exporter deliberately replaces several of them.

Real accounts, persistence and OTP were discussed earlier, but no database
provider or implementation has been approved. Neon is not currently required
or connected. There is no JavaScript framework migration to continue.

## Owner decisions to preserve

- Preserve the currently selected Tailvic visual design unless requested.
- Keep visible pages free of demo labels and displayed login credentials.
- Keep service/pricing pages focused on Tailvic; competitor comparisons and the
  published-reference pricing table were removed at the owner's request.
- Domain is registered at GoDaddy; Vercel hosts the existing project.
- Deploy through GitHub Actions on `main`. Repository collaboration does not
  require sharing the owner's account passwords or local CLI credentials.

## Next four weeks

Use the owner's requested tasks as the backlog. For a substantial feature,
start from `specs/change-template.md`, separate approved requirements from open
questions, then record implementation and verification evidence. Authentication,
persistence and real bookings are possible future work, not an instruction to
enable them automatically. Confirm product behaviour, data handling and hosting
requirements as part of those changes.

At the end of a task, update the relevant spec and docs if assumptions changed.
At the end of the handover period, update this file with the current baseline,
remaining work, known issues and links to important decisions/Actions runs.

## Context map

- `README.md`: setup and basic development commands.
- `AGENTS.md`: shared instructions and definition of completion.
- `CLAUDE.md`: Claude's entry point importing shared guidance.
- `docs/architecture.md`: source map and deployed/local behaviour.
- `docs/operations.md`: publishing, live verification, rollback and secrets.
- `specs/current-site.md`: current production behaviour to preserve.
- `specs/change-template.md`: lightweight feature specification.

Keep secrets and private customer information out of these documents. Source
and operational docs should evolve together; an external wiki is optional.
