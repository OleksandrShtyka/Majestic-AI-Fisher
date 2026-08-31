import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { SupportForm } from "@/components/SupportForm";
import { createClient } from "@/lib/supabase/server";
import { TrialPlan } from "@/components/TrialPlan";

type Ticket = { id:string; subject:string; message:string; category:string; status:string; created_at:string };

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data:{ user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");
  const { data: profile } = await supabase.from("profiles").select("username, role, subscription_status, subscription_expires_at, trial_used").eq("id", user.id).single();
  const { data: tickets } = await supabase.from("support_tickets").select("id,subject,message,category,status,created_at").order("created_at",{ascending:false}).limit(8);
  const active = profile?.subscription_status === "active" || profile?.subscription_status === "lifetime";
  return <AppShell admin={profile?.role === "admin"}><section className="content"><header className="content-head"><div><h1>Привет, {profile?.username || user.email}</h1><p>Управляйте доступом и обращениями в одном месте.</p></div><a className="button button-primary" href="/api/download">Скачать клиент</a></header><div className="dashboard-grid"><article className="card glass"><h3>Подписка</h3><strong>{profile?.subscription_status === "lifetime" ? "Вечная" : active ? "Активна" : "Неактивна"}</strong><p style={{color:"var(--muted)"}}>{profile?.subscription_expires_at ? `До ${new Date(profile.subscription_expires_at).toLocaleDateString("ru-RU")}` : active ? "Доступ без ограничения срока" : "Статус обновится после оплаты"}</p></article><TrialPlan available={!active && !profile?.trial_used} /><article className="card glass"><h3>Ваши обращения</h3><strong>{tickets?.length || 0}</strong><p style={{color:"var(--muted)"}}>Последние заявки в поддержку</p></article><article className="card glass"><h3>Роль</h3><strong>{profile?.role === "admin" ? "Администратор" : "Пользователь"}</strong><p style={{color:"var(--muted)"}}>Доступ определяется сервером</p></article><article className="card glass wide"><h3>Написать в поддержку</h3><SupportForm /></article><article className="card glass"><h3>Как это работает</h3><p style={{color:"var(--muted)",lineHeight:1.65}}>Выберите категорию, опишите проблему и приложите ссылку на материал в сообщении. Админ увидит обращение в рабочей очереди.</p></article><article className="card glass full"><h3>История обращений</h3><div className="ticket-list">{tickets?.length ? tickets.map((ticket:Ticket)=><div className="ticket" key={ticket.id}><div className="ticket-head"><strong>{ticket.subject}</strong><span className="badge">{ticket.status}</span></div><small style={{color:"var(--muted)"}}>{ticket.category} · {new Date(ticket.created_at).toLocaleString("ru-RU")}</small><p>{ticket.message}</p></div>) : <p style={{color:"var(--muted)"}}>Обращений пока нет.</p>}</div></article></div></section></AppShell>;
}
