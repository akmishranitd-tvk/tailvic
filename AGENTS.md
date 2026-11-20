# Tailvic agent instructions

## Working context

Read `README.md`, `docs/handover.md` and `docs/tasks.md` first. This handover is
about the deployed web experience at https://tailvic.in/. Source files and Git
history explain implementation; machine-specific setups, old ZIPs and backup
folders are not the operational baseline.

- Existing Vercel workspace/project: `tailvic/tailvic-demo`.
- Production is a generated static site, not the Flask database-backed server.
- Fixed admin/user credentials and live URLs are in README. Browser roles are
  not secure authentication and must not protect real private records.
- Registration, OTP, saved bookings, payments and editing are unfinished.
  Consult `docs/tasks.md`; do not assume code presence means a feature is live.

## Make a requested change

- Read `docs/architecture.md` to find the relevant source. Preserve the selected
  responsive design and existing stack unless the request changes them.
- Edit templates, content or static assets, not generated `public/` files.
- Keep service names, prices and business claims consistent. Do not add
  competitor-brand comparisons or published-reference tables to pricing pages.
- The owner requested no visible demo banners or displayed login credentials.
  Keep technical limitations clear in repository documentation and keep
  unavailable actions disabled or routed to truthful contact information.
- For substantial new behaviour, use `specs/change-template.md` with acceptance
  criteria and open decisions. Small copy/layout changes need no separate spec.
- Update the task checklist and relevant docs when delivered behaviour changes.
  Mark a task complete only after the deployed result is verified.

## Deploy and check the result

- Fetch shared changes before work. Preserve colleagues' edits and use your
  actual Git identity. Do not force-push shared history.
- When the user asks for a change and deployment, commit and push to `main` if
  repository policy permits. This triggers production deployment automatically;
  routine changes need no additional deployment confirmation or manual deploy.
- If working on a feature branch, publish by the team's normal merge into `main`.
  Without deployment authorization, use a feature branch. PR CI validates only;
  it does not create a live preview deployment.
- Watch the GitHub Actions run for the exact pushed SHA until completion.
  Checks and build must pass before production publishes. Fix failures and rerun.
- Verify the requested result at https://tailvic.in/ after deployment. Check
  actual content and interactions, not only HTTP 200. For layout changes inspect
  desktop and mobile, overflow, menus and sticky controls. Use browser screenshots
  when tools permit; disclose any visual/interactive checks you could not perform.
- Report the commit, pipeline outcome, live URL and verification evidence.

## Pipeline knowledge and boundaries

`.github/workflows/ci.yml` runs Python checks and the static export, then Vercel
pull/build/prebuilt production deployment. Python 3.11, Node 24, `uv` and Vercel
CLI 66.2.0 are the current build tools. See `docs/operations.md` for recovery.

Use the existing encrypted deployment secrets. Do not ask for tokens in chat,
commit private credentials, replace the existing project, change DNS, broaden
access or add a second deployment trigger for routine edits. Secure accounts and
persistence require an intentional architecture change with acceptance criteria.
