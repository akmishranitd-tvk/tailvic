# Current deployed site baseline

Status: implemented. Reviewed 2026-11-20. This documents current behaviour;
future owner-approved feature specs may intentionally change it.

## Product behaviour

- Tailvic's selected dog/cat grooming design works on desktop and mobile.
- Public navigation, services, guides and contact pages are available.
- Service prices and quote conditions remain consistent with source content.
- Service/pricing pages contain no competitor-brand comparisons, external
  competitor pricing links or published-reference comparison table.
- `/account/` accepts the fixed browser identities and displays the corresponding
  customer or admin presentation. It provides no server-side authorization.
- Registration, OTP, persistent account records, online booking submission,
  payments and editing are disabled in the deployed static version.
- Booking/careers calls to action lead to truthful contact information.
- Visible pages have no demo banners or displayed login credentials.

## Delivery behaviour

- The static export includes only intended public pages and approved assets.
- Customer databases, session keys and hosting credentials are not published.
- Pushes to `main` run checks/build/deployment through GitHub Actions.
- Pull requests run checks without publishing production.
- Production is served by the existing Tailvic Vercel project at `tailvic.in`.
- Failed checks/builds prevent that run from publishing its result.

## Verification

Run the existing application/export suite, build and serve `public/`, inspect
affected pages and interactions at desktop/mobile sizes, then verify the exact
successful Actions commit against the live domain after deployment. See
`docs/operations.md` for details and limits of HTTP-only checks.
