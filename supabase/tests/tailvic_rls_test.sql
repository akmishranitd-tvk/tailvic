begin;
select plan(17);

insert into auth.users (id, email, raw_user_meta_data)
values
  ('10000000-0000-4000-8000-000000000001', 'one@tailvic.test', '{"full_name":"Parent One","phone":"+917000000001"}'),
  ('20000000-0000-4000-8000-000000000002', 'two@tailvic.test', '{"full_name":"Parent Two","phone":"+917000000002"}');

select is((select count(*) from public.profiles), 2::bigint, 'auth signup creates a profile');
select is((select relrowsecurity from pg_class where oid = 'public.pets'::regclass), true, 'RLS is enabled for pets');
select is((select relrowsecurity from pg_class where oid = 'public.bookings'::regclass), true, 'RLS is enabled for bookings');

insert into public.slots (starts_at, ends_at, sector, is_published)
values (now() + interval '10 days', now() + interval '10 days 2 hours', '69', true),
       (now() + interval '11 days', now() + interval '11 days 2 hours', '70', false);

set local role authenticated;
set local "request.jwt.claims" = '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}';

select lives_ok(
  $$insert into public.pets (owner_id, name, species, breed)
    values (auth.uid(), 'Milo', 'dog', 'Indie')$$,
  'a customer can add their own pet'
);
select is((select count(*) from public.pets), 1::bigint, 'a customer sees their pet');
select is((select count(*) from public.slots), 1::bigint, 'a customer sees only published future slots');
select is((select count(*) from public.package_tariffs), 22::bigint, 'customers can read all approved tariff rows');
select is(
  (
    select jsonb_agg(jsonb_build_array(package_slug, species, size_key, coat_key, amount_paise)
                     order by package_slug, species, size_key, coat_key)
    from public.package_tariffs
  ),
  (
    select jsonb_agg(jsonb_build_array(package_slug, species, size_key, coat_key, amount_paise)
                     order by package_slug, species, size_key, coat_key)
    from (values
      ('bath-brush','dog','small','',99900),
      ('bath-brush','dog','medium','',119900),
      ('bath-brush','dog','large','',149900),
      ('bath-brush','dog','giant','',189900),
      ('hygiene-groom','dog','small','',129900),
      ('hygiene-groom','dog','medium','',159900),
      ('hygiene-groom','dog','large','',199900),
      ('hygiene-groom','dog','giant','',249900),
      ('full-groom','dog','small','',179900),
      ('full-groom','dog','medium','',219900),
      ('full-groom','dog','large','',269900),
      ('full-groom','dog','giant','',329900),
      ('signature-coat-spa','dog','small','',229900),
      ('signature-coat-spa','dog','medium','',269900),
      ('signature-coat-spa','dog','large','',329900),
      ('signature-coat-spa','dog','giant','',399900),
      ('cat-coat-refresh','cat','','short',99900),
      ('cat-coat-refresh','cat','','long',129900),
      ('cat-hygiene-groom','cat','','short',139900),
      ('cat-hygiene-groom','cat','','long',169900),
      ('cat-full-coat-groom','cat','','short',189900),
      ('cat-full-coat-groom','cat','','long',239900)
    ) as approved(package_slug, species, size_key, coat_key, amount_paise)
  ),
  'the database tariff matches all approved customer prices'
);

select lives_ok(
  $$insert into public.bookings
    (owner_id, pet_id, idempotency_key, service_slug, species, pet_name_snapshot,
     size_key, coat_key, preferred_at, address_line1_snapshot, sector_snapshot, postal_code_snapshot,
     status, starting_price_paise)
    values
    (auth.uid(), (select id from public.pets where owner_id=auth.uid() limit 1),
     '30000000-0000-4000-8000-000000000003', 'bath-brush', 'dog', 'untrusted name',
     'small', 'short', now() + interval '8 days', '1 Test Road', '69', '122001',
     'confirmed', 1)$$,
  'a customer can submit a pending request'
);
select is((select status from public.bookings limit 1), 'pending', 'new requests cannot self-confirm');
select is((select pet_name_snapshot from public.bookings limit 1), 'Milo', 'booking records use the selected pet name');
select is((select starting_price_paise from public.bookings limit 1), 99900, 'booking price is snapshotted from the tariff table');

set local "request.jwt.claims" = '{"sub":"20000000-0000-4000-8000-000000000002","role":"authenticated"}';
select is((select count(*) from public.pets), 0::bigint, 'another customer cannot read the first customer pet');
select is((select count(*) from public.bookings), 0::bigint, 'another customer cannot read the first customer booking');
select throws_ok(
  $$insert into public.bookings
    (owner_id, pet_id, idempotency_key, service_slug, species, pet_name_snapshot,
     size_key, coat_key, preferred_at, address_line1_snapshot, sector_snapshot, postal_code_snapshot)
    values
    (auth.uid(), (select id from public.pets where owner_id='10000000-0000-4000-8000-000000000001' limit 1),
     '40000000-0000-4000-8000-000000000004', 'bath-brush', 'dog', 'Milo',
     'small', 'short', now() + interval '8 days', '1 Test Road', '69', '122001')$$,
  'P0001',
  'Selected pet does not belong to this account.',
  'a customer cannot book another account pet'
);

reset role;
set local role anon;
select is((select count(*) from public.pets), 0::bigint, 'anonymous visitors cannot read pet profiles');
select is((select count(*) from public.package_tariffs), 22::bigint, 'anonymous visitors can read public package prices');

select * from finish();
rollback;
