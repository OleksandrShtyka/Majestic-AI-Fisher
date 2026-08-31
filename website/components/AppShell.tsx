import Link from "next/link";
import { logoutAction } from "@/lib/auth";

export function AppShell({ children, admin }: { children: React.ReactNode; admin: boolean }) {
  return <main className="app-shell"><aside className="side"><Link href="/" className="brand"><span className="brand-mark">M</span> MAJESTIC</Link><nav><Link href="/dashboard">Обзор</Link><a href="/api/download">Скачать клиент</a>{admin && <Link href="/dashboard/admin">Администрирование</Link>}</nav><form action={logoutAction} style={{marginTop:40}}><button className="button button-ghost" type="submit" style={{width:"100%"}}>Выйти</button></form></aside>{children}</main>;
}
