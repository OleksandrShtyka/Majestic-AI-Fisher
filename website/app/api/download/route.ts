import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const url = process.env.NEXT_PUBLIC_DOWNLOAD_URL;
  if (!url) return new NextResponse("Download URL is not configured", { status: 503 });
  try {
    const supabase = await createClient();
    const { data:{ user } } = await supabase.auth.getUser();
    if (user) await supabase.from("download_events").insert({ user_id:user.id });
  } catch { /* Download remains available when analytics is unavailable. */ }
  return NextResponse.redirect(url);
}
