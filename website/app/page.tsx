import Link from "next/link";

export default function HomePage() {
  return <main className="shell">
    <header className="topbar"><Link href="/" className="brand"><span className="brand-mark">M</span> MAJESTIC FISHER</Link><nav className="nav"><a href="#features">Возможности</a><Link href="/login">Личный кабинет</Link><Link className="button button-ghost" href="/login">Войти</Link></nav></header>
    <section className="hero">
      <div><span className="eyebrow"><i className="dot" /> Desktop automation workspace</span><h1>Рыбалка — под контролем.</h1><p>Единый кабинет для загрузки клиента, управления подпиской и обратной связи. Состояние аккаунта и обращения синхронизируются через защищённую базу Supabase.</p><div className="actions"><a className="button button-primary" href="/api/download">Скачать приложение</a><Link className="button button-ghost" href="/register">Получить доступ</Link></div></div>
      <div className="preview glass"><div className="preview-title"><span>Control center</span><span className="badge">ONLINE</span></div><div className="metric-grid"><div className="metric"><small>Статус лицензии</small><b>Активна</b></div><div className="metric"><small>Поддержка</small><b>24/7</b></div><div className="chart">{[35,53,42,68,59,84,75,94,83,100].map((height,index)=><i key={index} style={{height:`${height}%`}} />)}</div></div></div>
    </section>
    <section id="features" className="features"><article className="feature glass"><span className="icon">↓</span><h3>Актуальный клиент</h3><p>Загрузка последней версии из одного проверенного источника.</p></article><article className="feature glass"><span className="icon">◈</span><h3>Подписка</h3><p>Статус доступа, дата окончания и управление лицензией в кабинете.</p></article><article className="feature glass"><span className="icon">✦</span><h3>Поддержка</h3><p>Баг‑репорты, идеи и вопросы по оплате с прозрачным статусом обращения.</p></article></section>
  </main>;
}
