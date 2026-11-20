# Tailvic web development handover

Reviewed: 2026-11-20. This handover supports the owner's colleague and coding
agent developing the deployed website over the next four weeks.

## Starting point

- Repository: https://github.com/akmishranitd-tvk/tailvic (private).
- Production: https://tailvic.in/ and https://www.tailvic.in/.
- Alternate: https://tailvic-demo.vercel.app/.
- Vercel workspace/project: `tailvic/tailvic-demo`.
- Current admin/user credentials and live account links are in `README.md`.

Production publishes a static export of the selected Tailvic design. The
repository contains the complete source; other machine folders are not needed.
The website currently has public content, service filters, navigation, care
guides, contact links and fixed browser account roles. These roles are not secure
server-side authentication. No persistent application database is deployed.

The functional production baseline before handover documentation was `4eb5764`,
verified by https://github.com/akmishranitd-tvk/tailvic/actions/runs/44699449267.
Use current Git history and the exact latest successful deployment to establish
what is live now; dated notes do not override newer delivered changes.

## Recommended opening prompt

> Read AGENTS.md, README.md, docs/handover.md and docs/tasks.md. Focus on the
> deployed website at tailvic.in. Explain the relevant current behaviour before
> implementing my change. When I ask you to deploy, push through the documented
> main-branch pipeline, watch that commit's Actions run, and check my requested
> result on tailvic.in. Report what passed and anything you could not verify.

## Owner decisions to preserve

- Keep the selected responsive Tailvic visual design unless asked to change it.
- Keep visible pages free of demo labels and displayed login credentials.
  Repository documentation intentionally includes the fixed test identities.
- Keep service/pricing content focused on Tailvic; competitor comparisons and
  the published-reference table were removed at the owner's request.
- Use the existing Vercel project and GoDaddy-registered domain.
- Publish through GitHub Actions on `main`; no extra native Git deployment hook.
- Do not assume secure accounts, OTP, database or real bookings already work.

## Work still to do

See `docs/tasks.md` for the explicit unfinished-work checklist and dependencies.
There is no approved four-week feature order yet. Take the owner's next requests
as priorities, clarify missing acceptance criteria, and use the spec template for
substantial new behaviour. Future feature ideas are not approval to activate them.

After each delivered change, update affected docs and task status with commit,
Actions run and live verification evidence. At the end of four weeks update this
handover with current production behaviour, remaining work and important decisions.

## Documentation map

- `README.md`: web links, account details and deployment overview.
- `AGENTS.md` / `CLAUDE.md`: shared instructions and Claude entry point.
- `docs/tasks.md`: unfinished capabilities and operational follow-up.
- `docs/architecture.md`: deployed architecture and source map.
- `docs/operations.md`: pipeline, live verification, rollback and credential renewal.
- `specs/current-site.md`: behaviour currently supported by production.
- `specs/change-template.md`: lightweight feature specification.

Keep hosting credentials and real private data out of all documentation.
