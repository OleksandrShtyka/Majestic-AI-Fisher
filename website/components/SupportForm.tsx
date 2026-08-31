"use client";

import { FormEvent, useState } from "react";

export function SupportForm() {
  const [status, setStatus] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setStatus("Отправка…");
    const form = new FormData(event.currentTarget);
    const response = await fetch("/api/support", { method:"POST", body:form });
    const result = await response.json();
    setStatus(response.ok ? "Обращение отправлено." : result.error || "Не удалось отправить обращение.");
    if (response.ok) event.currentTarget.reset();
  }
  return <form className="support-form" onSubmit={submit}><label>Тема<input name="subject" minLength={3} maxLength={120} required /></label><label>Категория<select name="category" defaultValue="bug"><option value="bug">Баг‑репорт</option><option value="idea">Предложение</option><option value="payment">Оплата</option><option value="other">Другое</option></select></label><label>Сообщение<textarea name="message" minLength={10} maxLength={3000} required /></label><button className="button button-primary" type="submit">Отправить</button>{status && <span style={{alignSelf:"center",color:"var(--muted)"}}>{status}</span>}</form>;
}
