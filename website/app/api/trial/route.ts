import { NextResponse } from "next/server";
import { createAdminClient, createClient } from "@/lib/supabase/server";

export async function POST() {
  const session = await createClient();
  const { data: { user } } = await session.auth.getUser();
  if (!user) return NextResponse.json({ error: "Нужно войти в аккаунт." }, { status: 401 });
  const admin = createAdminClient();
  const { data: profile } = await admin.from("profiles").select("trial_used,subscription_status,is_banned").eq("id", user.id).maybeSingle();
  if (!profile || profile.is_banned || profile.trial_used || profile.subscription_status !== "inactive") return NextResponse.json({ error: "Пробный период недоступен." }, { status: 400 });
  const { error } = await admin.from("profiles").update({ trial_used: true, subscription_status: "active", subscription_expires_at: new Date(Date.now() + 3 * 86400000).toISOString() }).eq("id", user.id);
  return error ? NextResponse.json({ error: "Не удалось активировать пробный период." }, { status: 500 }) : NextResponse.json({ ok: true });
}
