# Development, deployment and recovery

Last reviewed: 2026-11-20.

## Normal edit-to-live workflow

1. Fetch/pull the current branch and inspect uncommitted changes. Work from this
   repository and current deployed behaviour as the baseline.
2. Implement the requested change and run relevant checks. Inspect the affected
   pages and links; CI builds the deployable static output.
3. If the owner requested deployment, commit and push to `main` according to
   repository policy. Otherwise use a feature branch for review.
4. Open https://github.com/akmishranitd-tvk/tailvic/actions and follow the run
   for that exact commit. Wait until the deployment step succeeds.
5. Verify the requested behaviour on https://tailvic.in/ and report evidence.

The workflow is `Validate and deploy Tailvic` in `.github/workflows/ci.yml`.
Pushes to `main` and manual runs selected on `main` deploy after checks pass.
Pull requests targeting `main` run checks without production deployment or
deployment credentials. Automatic PR preview deployments are not configured.
Merging into `main` causes a production deployment. Branch protection and
required-review rules have not been configured by this handover.

No additional deployment confirmation is needed when the owner explicitly asks
to make a change and deploy it, unless repository policy or the actual operation
requires it. A failed run or unavailable browser must be reported accurately.

## Build environment

- Python 3.11, declared in `.python-version` and the workflow.
- Python requirements in `requirements.txt`.
- Node.js 24 for deployment tooling; Vercel CLI pinned to 66.2.0.
- `uv` is installed on the runner because Vercel's Python build invokes it.
- Build/output configuration in `vercel.json`, framework `null`, output `public`.
- The workflow validates and exports on the GitHub runner, runs `vercel pull`,
  `vercel build --prod`, then `vercel deploy --prebuilt --prod --yes`.
- Vercel's configured build command also runs the checks before export.

Production deployment uses GitHub Actions and encrypted secrets, not Vercel's
native Git connector. The native connector refused this personal repository
because the Vercel account holder is a collaborator rather than its owner.
Do not add a second deployment trigger or replace the existing Vercel project.

## Live verification

Check the changed page and one related navigation path. Homepage, `/services/`
and `/account/` are useful baseline checks. Test interactive controls when
affected. For layout changes, inspect a desktop width (for example 1440px) and
a phone width (for example 390px), including overflow, menus and sticky buttons.
`/static/phone-preview.html` is also an interactive phone-frame preview.

For account changes, exercise the relevant fixed role and sign-out in a fresh
browser session. The account script uses session storage. Never enter real
private records or passwords into these browser-only accounts.

Use browser screenshots when available. If only HTTP/content checks are
possible, verify returned content as well as status and disclose the missing
visual/interactive verification. A screenshot of an old cached tab is not
deployment evidence. Confirm the Actions run corresponds to the intended SHA.

## Secrets and access

GitHub repository Actions secrets are `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and
`VERCEL_PROJECT_ID`. Secret values are never committed or included in handover
prompts. Existing repository access and these secrets are sufficient for the
workflow; colleagues do not need the previous developer's CLI sign-in.

The owner confirmed a Tailvic-project-scoped token with a 90-day expiry, saved
on 2026-11-20. Its exact expiry/scope must be checked in Vercel rather than
inferred from the GitHub secret timestamp. Arrange rotation with the owner
before expiry. Create a replacement with the approved scope/lifetime, update
`VERCEL_TOKEN` in GitHub repository Actions secrets, verify a deployment, then
revoke the superseded token. Do not broaden scope without owner authorization.

Anyone who can alter trusted repository workflows can potentially use the
deployment credential. Keep workflow changes reviewable and do not expose
secrets to pull-request code. Machine-specific sign-in files stay ignored.

## Domains

- Registrar and DNS host: GoDaddy.
- Root A record: `@` -> `76.76.21.21`, TTL 600 seconds at setup.
- `www` CNAME -> `tailvic.in`, TTL 1 hour at setup.
- Nameservers at setup: `ns29.domaincontrol.com`, `ns30.domaincontrol.com`.
- Both names map to the existing Vercel project and have HTTPS configured.

Routine deployments do not need DNS changes. If a domain still shows an old
GoDaddy parking page, compare authoritative and recursive DNS, check HTTPS and
the root URL, and account for cached `/lander` redirects. Do not call DNS setup
fully verified based only on an IP-pinned HTTP request; verify normal access too.

## Diagnose failed runs

| Symptom | First check |
| --- | --- |
| Tests fail | Open the failed test output and reproduce using the same source |
| Missing/invalid token | Verify the repository secret name and token expiry/scope with the owner |
| `spawn uv ENOENT` | Preserve the workflow's `uv` installation before Vercel build |
| Wrong project or forbidden access | Verify encrypted project/workspace IDs and token scope |
| Build passes but old page remains | Confirm deployment SHA, production alias and normal DNS/cache behaviour |
| Source feature is absent on the web | Check static-export overrides and the unfinished-feature checklist |

Fix the underlying issue and push a corrective commit, or rerun a failed run
after correcting a secret/environment issue. Use actual author identities and
respect provider permissions; do not bypass restrictions by spoofing authors.

## Rollback

For a source regression, revert the specific bad commit with `git revert`, push
the resulting commit to `main`, watch the deployment, and verify the live fix.
Preserve unrelated teammate work; do not reset/force-push shared history.
For urgent recovery, an authorized Vercel operator can promote a known-good
previous deployment in the existing project, then reconcile Git so the next
push does not restore the regression. Do not change domains to roll back code.
