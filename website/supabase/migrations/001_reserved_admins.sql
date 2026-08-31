-- Run this once in an existing Supabase project after schema.sql was applied.
-- New registrations named developer or pogo will receive admin + lifetime access.
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

-- Upgrade existing profiles with those reserved names as well.
update public.profiles
set role = 'admin', subscription_status = 'lifetime', subscription_expires_at = null
where username in ('developer', 'pogo');
