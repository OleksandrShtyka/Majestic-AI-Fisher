import Link from "next/link";
import { loginAction } from "@/lib/auth";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string; message?: string }> }) {
  const { error, message } = await searchParams;
  return <main className="auth-wrap"><section className="auth-card glass"><Link href="/" className="brand"><span className="brand-mark">M</span> MAJESTIC FISHER</Link><h1>С возвращением</h1><p>Войдите по никнейму или e-mail, чтобы открыть кабинет.</p><form action={loginAction} className="form"><label>Никнейм или e-mail<input name="identifier" autoComplete="username" required /></label><label>Пароль<input name="password" type="password" autoComplete="current-password" required /></label><button className="button button-primary">Войти</button></form>{error && <p className="notice">{error}</p>}{message && <p style={{ color:"var(--accent)" }}>{message}</p>}<p>Нет аккаунта? <Link href="/register" style={{color:"var(--accent)"}}>Создать</Link></p></section></main>;
}
