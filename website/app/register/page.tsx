import Link from "next/link";
import { registerAction } from "@/lib/auth";

export default async function RegisterPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return <main className="auth-wrap"><section className="auth-card glass"><Link href="/" className="brand"><span className="brand-mark">M</span> MAJESTIC FISHER</Link><h1>Создать аккаунт</h1><p>Никнейм можно использовать для входа вместо e-mail.</p><form action={registerAction} className="form"><label>Никнейм<input name="username" minLength={3} maxLength={24} autoComplete="username" required /></label><label>E-mail<input name="email" type="email" autoComplete="email" required /></label><label>Пароль<input name="password" type="password" minLength={8} autoComplete="new-password" required /></label><button className="button button-primary">Зарегистрироваться</button></form>{error && <p className="notice">{error}</p>}<p>Уже есть аккаунт? <Link href="/login" style={{color:"var(--accent)"}}>Войти</Link></p></section></main>;
}
