# Majestic AI Fisher Web

Next.js App Router portal for Vercel with Supabase Auth, profiles, subscriptions, support tickets, downloads, and admin analytics.

## Local setup

1. Create a Supabase project and run [`supabase/schema.sql`](./supabase/schema.sql) in its SQL Editor.
2. In Supabase Auth, enable email/password sign-in and configure your Vercel URL as the site/redirect URL.
3. Copy `.env.example` to `.env.local`, then insert the Supabase URL, publishable key, service-role key, and release URL.
4. Run `npm install` and `npm run dev` from this directory.

## Deploy to Vercel

Import the `website` directory as the project root, copy the four environment variables from `.env.local` into Vercel Project Settings, then deploy. `SUPABASE_SERVICE_ROLE_KEY` must remain server-only and must never receive an `NEXT_PUBLIC_` prefix.

The reserved usernames `developer` and `pogo` receive an admin role and lifetime subscription during signup. On a project where the schema was already installed, run [`supabase/migrations/001_reserved_admins.sql`](./supabase/migrations/001_reserved_admins.sql) once.
