"use client";

import { useState } from "react";

export function TrialPlan({ available }: { available: boolean }) {
  const [message, setMessage] = useState("");
  async function startTrial() {
    const response = await fetch("/api/trial", { method: "POST" });
    const data = await response.json();
    setMessage(response.ok ? "Пробный доступ активирован на 3 дня." : data.error || "Не удалось включить trial.");
    if (response.ok) window.setTimeout(() => window.location.reload(), 700);
  }
  return <article className="card glass trial-plan"><h3>Trial · 3 дня</h3><strong>Бесплатно</strong><p>Один раз для каждого аккаунта. Полный доступ к клиенту на 72 часа.</p>{available ? <button className="button button-primary" onClick={startTrial}>Запустить trial</button> : <span className="badge">{message || "Недоступен"}</span>}{message && available && <small>{message}</small>}</article>;
}
