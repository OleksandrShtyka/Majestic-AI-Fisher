import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
  const form = await request.formData();
  const subject = String(form.get("subject") || "").trim();
  const category = String(form.get("category") || "other").trim();
  const message = String(form.get("message") || "").trim();
  if (subject.length < 3 || message.length < 10 || message.length > 3000) return NextResponse.json({ error:"Проверьте тему и текст обращения." },{status:400});
  const supabase = await createClient();
  const { data:{user} } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({error:"Нужно войти в аккаунт."},{status:401});
  const { error } = await supabase.from("support_tickets").insert({ user_id:user.id, subject, category, message });
  if (error) return NextResponse.json({error:"Не удалось сохранить обращение."},{status:500});
  return NextResponse.json({ ok:true });
}
