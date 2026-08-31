create type public.app_role as enum ('user', 'admin');
create type public.subscription_state as enum ('inactive', 'active', 'lifetime');
create type public.ticket_status as enum ('open', 'in_progress', 'resolved');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  username text not null unique check (username ~ '^[a-z0-9_]{3,24}$'),
  role public.app_role not null default 'user',
  subscription_status public.subscription_state not null default 'inactive',
  subscription_expires_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.support_tickets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  subject text not null check (char_length(subject) between 3 and 120),
  category text not null check (category in ('bug','idea','payment','other')),
  message text not null check (char_length(message) between 10 and 3000),
  status public.ticket_status not null default 'open',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.download_events (
  id bigint generated always as identity primary key,
  user_id uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id,email,username,role,subscription_status)
  values (
    new.id,
    lower(new.email),
    lower(new.raw_user_meta_data->>'username'),
    case when lower(new.raw_user_meta_data->>'username') in ('developer', 'pogo') then 'admin'::public.app_role else 'user'::public.app_role end,
    case when lower(new.raw_user_meta_data->>'username') in ('developer', 'pogo') then 'lifetime'::public.subscription_state else 'inactive'::public.subscription_state end
  );
  return new;
end;
$$;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();

create or replace function public.current_is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role = 'admin');
$$;

alter table public.profiles enable row level security;
alter table public.support_tickets enable row level security;
alter table public.download_events enable row level security;

create policy "profiles: read own or admin" on public.profiles for select using (id = auth.uid() or public.current_is_admin());
create policy "tickets: user reads own or admin reads all" on public.support_tickets for select using (user_id = auth.uid() or public.current_is_admin());
create policy "tickets: user creates own" on public.support_tickets for insert with check (user_id = auth.uid());
create policy "tickets: admin updates" on public.support_tickets for update using (public.current_is_admin()) with check (public.current_is_admin());
create policy "downloads: user creates own" on public.download_events for insert with check (user_id = auth.uid());
create policy "downloads: admin reads" on public.download_events for select using (public.current_is_admin());

-- Reserved admin usernames are developer and pogo. They receive admin and
-- lifetime access during signup. Protect these names with strong passwords.
