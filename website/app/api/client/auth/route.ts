import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
  const { identifier, password } = await request.json() as { identifier?: string; password?: string };
  const login = identifier?.trim().toLowerCase() || "";
  if (!login || !password) return NextResponse.json({ error: "Укажите логин и пароль." }, { status: 400 });
  const admin = createAdminClient();
  let email = login;
  if (!login.includes("@")) { const { data } = await admin.from("profiles").select("email").eq("username", login).maybeSingle(); email = data?.email || ""; }
  if (!email) return NextResponse.json({ error: "Неверный логин или пароль." }, { status: 401 });
  const { data: auth, error: authError } = await admin.auth.signInWithPassword({ email, password });
  if (authError || !auth.user) return NextResponse.json({ error: "Неверный логин или пароль." }, { status: 401 });
  const { data: profile } = await admin.from("profiles").select("username,role,subscription_status,subscription_expires_at,is_banned").eq("id", auth.user.id).maybeSingle();
  if (!profile || profile.is_banned) return NextResponse.json({ error: "Доступ к аккаунту ограничен." }, { status: 403 });
  const active = profile.subscription_status === "lifetime" || (profile.subscription_status === "active" && (!profile.subscription_expires_at || new Date(profile.subscription_expires_at) > new Date()));
  return NextResponse.json({ ok: true, profile: { username: profile.username, role: profile.role, subscription_status: profile.subscription_status, active } });
}
