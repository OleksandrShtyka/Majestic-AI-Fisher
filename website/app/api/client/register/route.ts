import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
  const { username, email, password } = await request.json() as { username?: string; email?: string; password?: string };
  const name = username?.trim().toLowerCase() || ""; const mail = email?.trim().toLowerCase() || "";
  if (!/^[a-z0-9_]{3,24}$/.test(name) || !mail.includes("@") || !password || password.length < 8) return NextResponse.json({ error: "Укажите ник, e-mail и пароль от 8 символов." }, { status: 400 });
  const admin = createAdminClient();
  const { data: existing } = await admin.from("profiles").select("id").eq("username", name).maybeSingle();
  if (existing) return NextResponse.json({ error: "Этот ник уже занят." }, { status: 409 });
  const { data: auth, error } = await admin.auth.admin.createUser({ email: mail, password, email_confirm: true, user_metadata: { username: name } });
  if (error || !auth.user) return NextResponse.json({ error: "Не удалось создать аккаунт." }, { status: 400 });
  const { error: profileError } = await admin.from("profiles").update({ trial_used: true, subscription_status: "active", subscription_expires_at: new Date(Date.now() + 3 * 86400000).toISOString() }).eq("id", auth.user.id);
  return profileError ? NextResponse.json({ error: "Аккаунт создан, но не удалось включить trial." }, { status: 500 }) : NextResponse.json({ ok: true });
}
