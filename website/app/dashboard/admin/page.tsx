import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { createClient } from "@/lib/supabase/server";

export default async function AdminPage() {
  const supabase = await createClient(); const { data:{user} } = await supabase.auth.getUser(); if (!user) redirect("/login");
  const { data: profile } = await supabase.from("profiles").select("role").eq("id",user.id).single(); if (profile?.role !== "admin") redirect("/dashboard");
  const [{ count: users }, { count: active }, { data: tickets }, { data: downloads }] = await Promise.all([
    supabase.from("profiles").select("id",{count:"exact",head:true}),
    supabase.from("profiles").select("id",{count:"exact",head:true}).eq("subscription_status","active"),
    supabase.from("support_tickets").select("id,subject,message,category,status,created_at,profiles(username)").order("created_at",{ascending:false}).limit(30),
    supabase.from("download_events").select("id",{count:"exact",head:true}),
  ]);
  return <AppShell admin><section className="content"><header className="content-head"><div><h1>Администрирование</h1><p>Аналитика продукта и очередь поддержки.</p></div></header><div className="dashboard-grid"><article className="card glass"><h3>Пользователи</h3><strong>{Number(users ?? 0)}</strong></article><article className="card glass"><h3>Активные подписки</h3><strong>{Number(active ?? 0)}</strong></article><article className="card glass"><h3>Загрузки</h3><strong>{Number(downloads ?? 0)}</strong></article><article className="card glass full"><h3>Все репорты поддержки</h3><div className="ticket-list">{tickets?.map((ticket:any)=><div className="ticket" key={ticket.id}><div className="ticket-head"><strong>{ticket.subject}</strong><span className="badge">{ticket.status}</span></div><small style={{color:"var(--muted)"}}>{ticket.profiles?.username || "Удалённый пользователь"} · {ticket.category} · {new Date(ticket.created_at).toLocaleString("ru-RU")}</small><p>{ticket.message}</p></div>)}</div></article></div></section></AppShell>;
}
