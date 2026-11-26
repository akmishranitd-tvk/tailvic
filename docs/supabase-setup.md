# Supabase setup for Tailvic

Status: foundation prepared; no Supabase project is connected yet.

This project will use Supabase Auth, Postgres with row-level security, and a
private Storage bucket for pet photos. The customer website must use only the
project URL and publishable key. Never place a Supabase secret/service-role key
in browser JavaScript, generated static files, GitHub source, or this document.

## What the migration creates

- Customer profiles linked to Supabase Auth identities.
- Multiple pets and saved home addresses per customer.
- A price catalog containing the approved 22 size/coat tariff combinations.
- Published appointment slots and pending booking requests.
- Price snapshots derived in Postgres, idempotency keys, and one active request
  per published slot.
- Owner-scoped RLS for profiles, pets, addresses, and booking history.
- Read-only public access to approved prices and published future slots.
- A private `pet-photos` bucket restricted by the owner's UUID folder.
- A trusted staff role based on server-managed `app_metadata`; customer-editable
  profile data cannot assign staff privileges.

New requests always start as **pending**. A customer cannot set the booking status
or price. A preferred time without a published slot is recorded as a request,
not represented as confirmed availability. Payment is not part of this migration.

## Create and configure the project

1. Create a Supabase project for Tailvic. Choose a region nearest Gurugram from
   the regions actually available in the dashboard. Keep the database password
   in the password manager; it is not needed in website code.
2. Apply `supabase/migrations/20261126160000_tailvic_booking_core.sql` through
   the Supabase SQL editor or Supabase CLI. Do not run it against a project that
   already has customer data without first inspecting its schema.
3. In Authentication → URL Configuration, set the Site URL to
   `https://tailvic.in` and add these exact redirect URLs:
   `https://tailvic.in/account/`, `https://www.tailvic.in/account/`, and the
   local development callback used by the app.
4. Enable email sign-up and confirmation. The app can use email OTP/magic-link
   authentication; production email delivery needs a verified sender and a
   configured SMTP provider before customers rely on it.
5. Confirm the `pet-photos` storage bucket is private and retain its 5 MB image
   limit and JPEG, PNG, and WebP allowlist.
6. Copy the project URL and publishable key from the Supabase project settings.
   Add them as deployment environment variables. These are public client values;
   security depends on the policies in the migration. Never add the secret key.
7. Create the first Tailvic staff account through Supabase Auth, then assign
   `app_metadata.tailvic_role = admin` through the trusted Supabase dashboard or
   Admin API. Do not set this field from the customer browser.
8. Publish real availability only after Tailvic confirms the working hours,
   appointment length, buffers, and process for accepting/declining requests.

## Local verification

The repository includes `supabase/config.toml` and pgTAP checks in
`supabase/tests/`. With Docker and the Supabase CLI installed:

```sh
supabase start
supabase test db
supabase stop
```

Local Auth email is captured by the local mail inbox; no customer email should
be used for these tests. The CI run should execute these same migration and RLS
checks before any production deployment.

## Still needed before live customer data

- A Tailvic Supabase project and its public URL/key configured in deployment.
- Production email/SMTP sender, auth redirect confirmation, and tested delivery.
- Business-confirmed slots, duration/buffers, and who manages them.
- A privacy notice that accurately describes account, pet, photo, address, and
  appointment data, its retention, and customer deletion requests.
- Customer-facing Supabase auth, pet-profile, and booking screens wired to these
  tables and tested end to end.

Until those are complete, production must keep the existing contact-first flow.
