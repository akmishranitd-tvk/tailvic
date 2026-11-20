# Unfinished work and follow-up

Reviewed: 2026-11-20. These items are not implemented in the deployed web solution
unless marked complete with deployment evidence. This checklist gives context;
the owner sets priorities and approves product/provider decisions. It is not
permission to implement everything or change business behaviour automatically.

## Features not available on tailvic.in

- [ ] Secure server-side customer/admin authentication and authorization.
  Current JavaScript roles only change presentation and cannot protect private data.
- [ ] Persistent production data storage. No production database is connected;
  define a storage/backend plan before saving users, pets, bookings or admin edits.
- [ ] Email OTP sign-in. Email was the preferred channel, but no provider,
  delivery integration, expiry/retry rules or abuse protection is implemented.
- [ ] New-user registration and account lifecycle, if the owner enables it.
  The current intended behaviour is fixed existing accounts with registration closed.
- [ ] Saved customer profiles, pets and appointment history using real data.
- [ ] Real booking requests, published slot availability, quotes and confirmation.
  The current booking page offers contact information instead of saving requests.
- [ ] Admin appointment/availability/service editing backed by real authorization
  and persistent storage. Current production dashboards show empty states and
  public service information.
- [ ] Payment processing and verified payment status, if requested. No production
  gateway/bank integration or automatic settlement verification is present.
- [ ] Groomer recruitment submissions and authorized review, if requested.
  The careers page currently directs visitors to contact the team.
- [ ] Real reminders, memberships and planned services, if requested. Promotional
  or planned-content sections do not imply an operational service integration.

Authentication and storage are dependencies for private saved records. Define
acceptance criteria, data handling and deployment support in a feature spec
before enabling these capabilities. Backend source in the repository does not
mean these features are deployed or ready for real customer use.

## Web launch and operational follow-up

- [ ] Decide whether the site should be indexed by search engines. Current
  export robots/meta directives and Vercel headers deliberately disable indexing.
  If enabling SEO, update all relevant directives, canonical URLs and sitemap
  delivery together, then verify the deployed result.
- [ ] Review remaining example/illustrative business content and confirm actual
  staff, qualifications, services, coverage, prices and policies with the owner.
- [ ] Verify that hosting plan/terms fit the intended commercial launch before
  treating the static website as a full operating business platform.
- [ ] Confirm the deployment token's exact expiry/scope in Vercel and arrange
  renewal before expiry. Owner requested a 90-day project-scoped credential.
- [ ] Decide whether to enforce branch protection/required review on `main`.
  These rules were not configured during the handover.

## Routine completion evidence

For a task marked complete, record the relevant spec/issue, commit, successful
Actions run, live URL, and tested user behaviour (including desktop/mobile for
layout changes). Distinguish "implemented" from "deployed and verified". Keep
unverified behaviour and outstanding owner decisions explicit.
