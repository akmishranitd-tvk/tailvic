-- Tailvic Supabase foundation: profiles, pets, service availability and booking requests.
-- No service-role key is used by the customer application.
create extension if not exists pgcrypto;

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.is_tailvic_admin()
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select coalesce((auth.jwt() -> 'app_metadata' ->> 'tailvic_role') = 'admin', false);
$$;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default '' check (length(full_name) <= 100),
  phone text not null default '' check (length(phone) <= 25),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, full_name, phone)
  values (
    new.id,
    left(coalesce(new.raw_user_meta_data ->> 'full_name', ''), 100),
    left(coalesce(new.raw_user_meta_data ->> 'phone', ''), 25)
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();

create trigger profiles_touch_updated_at before update on public.profiles
  for each row execute function public.touch_updated_at();

create table public.pets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id) on delete cascade,
  name text not null check (length(trim(name)) between 1 and 80),
  species text not null check (species in ('dog', 'cat')),
  breed text not null default '' check (length(breed) <= 100),
  gender text check (gender is null or gender in ('female', 'male', 'unknown')),
  date_of_birth date,
  approximate_age text check (approximate_age is null or length(approximate_age) <= 40),
  weight_kg numeric(6,2) check (weight_kg is null or weight_kg between 0.1 and 200),
  coat_type text check (coat_type is null or coat_type in ('short', 'long', 'double', 'curly', 'wire', 'other')),
  photo_path text check (photo_path is null or length(photo_path) <= 500),
  grooming_instructions text not null default '' check (length(grooming_instructions) <= 1200),
  behavioural_notes text not null default '' check (length(behavioural_notes) <= 1200),
  sensitivities text not null default '' check (length(sensitivities) <= 1200),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index pets_owner_id_idx on public.pets(owner_id);
create trigger pets_touch_updated_at before update on public.pets
  for each row execute function public.touch_updated_at();

create table public.addresses (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id) on delete cascade,
  label text not null default 'Home' check (length(label) <= 40),
  address_line1 text not null check (length(trim(address_line1)) between 1 and 200),
  address_line2 text not null default '' check (length(address_line2) <= 200),
  sector text not null check (sector in ('69', '70', '71')),
  postal_code text not null check (postal_code ~ '^[0-9]{6}$'),
  is_default boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index addresses_owner_id_idx on public.addresses(owner_id);
create unique index addresses_one_default_per_owner_idx
  on public.addresses(owner_id) where is_default;
create trigger addresses_touch_updated_at before update on public.addresses
  for each row execute function public.touch_updated_at();

-- Publicly readable, backend-validated tariff snapshots. Writes are migration-only.
create table public.package_tariffs (
  package_slug text not null,
  species text not null check (species in ('dog', 'cat')),
  size_key text not null default '',
  coat_key text not null default '',
  amount_paise integer not null check (amount_paise > 0),
  primary key (package_slug, species, size_key, coat_key),
  check (
    (species = 'dog' and size_key in ('small', 'medium', 'large', 'giant') and coat_key = '')
    or
    (species = 'cat' and coat_key in ('short', 'long') and size_key = '')
  )
);
alter table public.package_tariffs enable row level security;
revoke all on public.package_tariffs from anon, authenticated;
grant select on public.package_tariffs to anon, authenticated;
create policy package_tariffs_are_publicly_readable
  on public.package_tariffs for select to anon, authenticated using (true);

insert into public.package_tariffs (package_slug, species, size_key, coat_key, amount_paise) values
  ('bath-brush','dog','small',null,99900),
  ('bath-brush','dog','medium',null,119900),
  ('bath-brush','dog','large',null,149900),
  ('bath-brush','dog','giant',null,189900),
  ('hygiene-groom','dog','small',null,129900),
  ('hygiene-groom','dog','medium',null,159900),
  ('hygiene-groom','dog','large',null,199900),
  ('hygiene-groom','dog','giant',null,249900),
  ('full-groom','dog','small',null,179900),
  ('full-groom','dog','medium',null,219900),
  ('full-groom','dog','large',null,269900),
  ('full-groom','dog','giant',null,329900),
  ('signature-coat-spa','dog','small',null,229900),
  ('signature-coat-spa','dog','medium',null,269900),
  ('signature-coat-spa','dog','large',null,329900),
  ('signature-coat-spa','dog','giant',null,399900),
  ('cat-coat-refresh','cat',null,'short',99900),
  ('cat-coat-refresh','cat',null,'long',129900),
  ('cat-hygiene-groom','cat',null,'short',139900),
  ('cat-hygiene-groom','cat',null,'long',169900),
  ('cat-full-coat-groom','cat',null,'short',189900),
  ('cat-full-coat-groom','cat',null,'long',239900);

create table public.slots (
  id uuid primary key default gen_random_uuid(),
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  sector text check (sector is null or sector in ('69', '70', '71')),
  is_published boolean not null default false,
  created_at timestamptz not null default now(),
  check (ends_at > starts_at)
);
create index slots_public_starts_at_idx on public.slots(starts_at) where is_published;

create table public.bookings (
  id uuid primary key default gen_random_uuid(),
  reference_code text not null unique default ('TV-' || upper(encode(gen_random_bytes(5), 'hex'))),
  owner_id uuid not null references public.profiles(id),
  pet_id uuid not null references public.pets(id),
  idempotency_key uuid not null,
  service_slug text not null,
  species text not null check (species in ('dog', 'cat')),
  pet_name_snapshot text not null check (length(pet_name_snapshot) between 1 and 80),
  size_key text,
  coat_key text,
  slot_id uuid references public.slots(id),
  preferred_at timestamptz,
  address_line1_snapshot text not null check (length(trim(address_line1_snapshot)) between 1 and 200),
  address_line2_snapshot text not null default '' check (length(address_line2_snapshot) <= 200),
  sector_snapshot text not null check (sector_snapshot in ('69', '70', '71')),
  postal_code_snapshot text not null check (postal_code_snapshot ~ '^[0-9]{6}$'),
  care_notes text not null default '' check (length(care_notes) <= 1200),
  status text not null default 'pending' check (status in ('pending', 'confirmed', 'completed', 'cancelled', 'declined')),
  starting_price_paise integer check (starting_price_paise is null or starting_price_paise > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, idempotency_key),
  check (
    (species = 'dog' and size_key in ('small', 'medium', 'large', 'giant') and coat_key is not null)
    or
    (species = 'cat' and coat_key in ('short', 'long') and size_key is null)
  ),
  check ((slot_id is not null) or (preferred_at is not null))
);
create index bookings_owner_created_idx on public.bookings(owner_id, created_at desc);
create index bookings_pet_created_idx on public.bookings(pet_id, created_at desc);
create unique index bookings_one_active_per_slot_idx
  on public.bookings(slot_id)
  where slot_id is not null and status in ('pending', 'confirmed');
create trigger bookings_touch_updated_at before update on public.bookings
  for each row execute function public.touch_updated_at();

create or replace function public.prepare_booking_request()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_pet public.pets%rowtype;
  v_slot public.slots%rowtype;
  v_price integer;
begin
  if auth.uid() is not null and new.owner_id is distinct from auth.uid() then
    raise exception 'Booking owner must match the signed-in account.';
  end if;

  select * into v_pet
  from public.pets
  where id = new.pet_id and owner_id = new.owner_id and is_active = true;
  if not found then
    raise exception 'Selected pet does not belong to this account.';
  end if;
  if new.species <> v_pet.species then
    raise exception 'Booking pet type must match the selected pet.';
  end if;
  new.pet_name_snapshot = v_pet.name;

  if new.slot_id is not null then
    select * into v_slot from public.slots
    where id = new.slot_id and is_published = true and starts_at > now()
    for update;
    if not found then
      raise exception 'That appointment time is no longer available.';
    end if;
    if v_slot.sector is not null and v_slot.sector <> new.sector_snapshot then
      raise exception 'That appointment time is not available in the selected sector.';
    end if;
    new.preferred_at = v_slot.starts_at;
  elsif new.preferred_at is null or new.preferred_at <= now() then
    raise exception 'Choose a future published time or request a future preferred time.';
  end if;

  if new.service_slug = 'express-care' then
    v_price := null;
  else
    select amount_paise into v_price
    from public.package_tariffs
    where package_slug = new.service_slug
      and species = new.species
      and ((new.species = 'dog' and size_key = new.size_key and coat_key = '')
        or (new.species = 'cat' and size_key = '' and coat_key = new.coat_key));
    if not found then
      raise exception 'The selected package and size or coat are not in the approved tariff.';
    end if;
  end if;

  new.status := 'pending';
  new.starting_price_paise := v_price;
  return new;
end;
$$;

create trigger bookings_prepare_request before insert on public.bookings
  for each row execute function public.prepare_booking_request();

alter table public.profiles enable row level security;
alter table public.pets enable row level security;
alter table public.addresses enable row level security;
alter table public.slots enable row level security;
alter table public.bookings enable row level security;

revoke all on public.profiles, public.pets, public.addresses, public.slots, public.bookings from anon, authenticated;
grant select, update on public.profiles to authenticated;
grant select, insert, update, delete on public.pets, public.addresses to authenticated;
grant select on public.slots to anon, authenticated;
grant insert, update, delete on public.slots to authenticated;
grant select, insert, update on public.bookings to authenticated;

create policy profiles_read_own on public.profiles
  for select to authenticated using (id = (select auth.uid()));
create policy profiles_update_own on public.profiles
  for update to authenticated using (id = (select auth.uid())) with check (id = (select auth.uid()));

create policy pets_owner_access on public.pets
  for all to authenticated using (owner_id = (select auth.uid()))
  with check (owner_id = (select auth.uid()));

create policy addresses_owner_access on public.addresses
  for all to authenticated using (owner_id = (select auth.uid()))
  with check (owner_id = (select auth.uid()));

create policy published_future_slots_are_readable on public.slots
  for select to anon, authenticated using (is_published and starts_at > now());
create policy tailvic_admins_manage_slots on public.slots
  for all to authenticated using (public.is_tailvic_admin())
  with check (public.is_tailvic_admin());

create policy customers_read_own_bookings on public.bookings
  for select to authenticated using (owner_id = (select auth.uid()));
create policy customers_create_own_bookings on public.bookings
  for insert to authenticated with check (
    owner_id = (select auth.uid())
    and exists (
      select 1 from public.pets p
      where p.id = pet_id and p.owner_id = (select auth.uid())
    )
  );
create policy tailvic_admins_read_bookings on public.bookings
  for select to authenticated using (public.is_tailvic_admin());
create policy tailvic_admins_update_bookings on public.bookings
  for update to authenticated using (public.is_tailvic_admin())
  with check (public.is_tailvic_admin());

-- Pet photographs are private. Object keys start with the authenticated user UUID.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('pet-photos', 'pet-photos', false, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy pet_photos_read_own on storage.objects
  for select to authenticated using (
    bucket_id = 'pet-photos' and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy pet_photos_upload_own on storage.objects
  for insert to authenticated with check (
    bucket_id = 'pet-photos' and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy pet_photos_update_own on storage.objects
  for update to authenticated using (
    bucket_id = 'pet-photos' and (storage.foldername(name))[1] = (select auth.uid())::text
  ) with check (
    bucket_id = 'pet-photos' and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy pet_photos_delete_own on storage.objects
  for delete to authenticated using (
    bucket_id = 'pet-photos' and (storage.foldername(name))[1] = (select auth.uid())::text
  );

-- Only Tailvic staff assigned through trusted app_metadata can manage operational data.
