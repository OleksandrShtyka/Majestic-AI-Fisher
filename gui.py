import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import DatabaseManager
from bot_engine import FishingEngine
from supportsystem import SupportManager
from config import DATASET_DIR

ctk.set_appearance_mode("Dark")


class ToastNotification(ctk.CTkToplevel):
    def __init__(self, parent, message, duration=2000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        
        window_width = 300
        window_height = 50
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (window_width // 2)
        y = parent.winfo_y() + parent.winfo_height() - 80
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        frame = ctk.CTkFrame(self, fg_color="#1f538d", corner_radius=8)
        frame.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(frame, text=message, text_color="white", font=("Arial", 12, "bold"))
        label.pack(expand=True)
        
        self.after(duration, self.destroy)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Majestic RP — AI Fishing Bot Suite")
        self.geometry("900x600")
        self.resizable(False, False)
        self.configure(fg_color="#121214")

        self.db = DatabaseManager()
        self.engine = FishingEngine()
        self.support_manager = SupportManager()
        self.user = None
        self.selected_ticket_id = None

        # Clean thread stop on close window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.render_auth()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # ==================== ЭКРАН 1: АВТОРИЗАЦИЯ ====================
    def render_auth(self):
        self.clear()

        card = ctk.CTkFrame(self, width=360, height=440, fg_color="#18181B", corner_radius=14)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="AI FISHING SYSTEM", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#FFFFFF").pack(pady=(30, 4))
        ctk.CTkLabel(card, text="Вход & Активация подписки", font=ctk.CTkFont(size=11), text_color="#71717A").pack(
            pady=(0, 20))

        self.ent_user = ctk.CTkEntry(card, placeholder_text="Логин", width=270, height=42, fg_color="#27272A")
        self.ent_user.pack(pady=6)

        self.ent_pass = ctk.CTkEntry(card, placeholder_text="Пароль", show="*", width=270, height=42,
                                     fg_color="#27272A")
        self.ent_pass.pack(pady=6)

        btn_login = ctk.CTkButton(card, text="ВОЙТИ В СИСТЕМУ", font=ctk.CTkFont(size=12, weight="bold"), width=270,
                                  height=42, fg_color="#E11D48", hover_color="#BE123C", command=self.on_login)
        btn_login.pack(pady=(16, 8))

        btn_reg = ctk.CTkButton(card, text="Создать аккаунт (3 дня триала)", font=ctk.CTkFont(size=11),
                                fg_color="transparent", text_color="#A1A1AA", command=self.on_register)
        btn_reg.pack()

    def on_login(self):
        u, p = self.ent_user.get(), self.ent_pass.get()
        ok, msg = self.db.login(u, p)
        if ok:
            sub_ok, sub_msg = self.db.check_subscription(u)
            if not sub_ok:
                messagebox.showerror("Ошибка подписки", sub_msg)
                return
            self.user = u
            self.render_dashboard()
        else:
            messagebox.showerror("Ошибка", msg)

    def on_register(self):
        u, p = self.ent_user.get(), self.ent_pass.get()
        ok, msg = self.db.register(u, p)
        if ok:
            messagebox.showinfo("Успех", msg)
        else:
            messagebox.showerror("Ошибка", msg)

    # ==================== ЭКРАН 2: ГЛАВНАЯ ПАНЕЛЬ ====================
    def render_dashboard(self):
        self.clear()

        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#18181B")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="🤖 AI ENGINE", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF").pack(
            pady=(25, 20))

        self.b_main = ctk.CTkButton(sidebar, text="🎮 Главный Движок", anchor="w", fg_color="#27272A",
                                    command=lambda: self.tab("main"))
        self.b_main.pack(fill="x", padx=12, pady=4)

        self.b_ai = ctk.CTkButton(sidebar, text="🧠 Обучение на Медиа", anchor="w", fg_color="transparent",
                                  text_color="#A1A1AA", command=lambda: self.tab("ai"))
        self.b_ai.pack(fill="x", padx=12, pady=4)

        self.b_shop = ctk.CTkButton(sidebar, text="💎 Подписка & Ключи", anchor="w", fg_color="transparent",
                                    text_color="#A1A1AA", command=lambda: self.tab("shop"))
        self.b_shop.pack(fill="x", padx=12, pady=4)

        self.b_set = ctk.CTkButton(sidebar, text="⚙️ Настройки бота", anchor="w", fg_color="transparent",
                                   text_color="#A1A1AA", command=lambda: self.tab("settings"))
        self.b_set.pack(fill="x", padx=12, pady=4)

        self.b_support = ctk.CTkButton(sidebar, text="🛠️ Поддержка", anchor="w", fg_color="transparent",
                                       text_color="#A1A1AA", command=lambda: self.tab("support"))
        self.b_support.pack(fill="x", padx=12, pady=4)

        if self.db.is_developer(self.user):
            self.b_admin = ctk.CTkButton(sidebar, text="👑 Админ-Кабинет", anchor="w", fg_color="transparent",
                                           text_color="#F59E0B", command=lambda: self.tab("admin"))
            self.b_admin.pack(fill="x", padx=12, pady=4)
        else:
            self.b_admin = None

        u_card = ctk.CTkFrame(sidebar, fg_color="#27272A", corner_radius=10)
        u_card.pack(side="bottom", fill="x", padx=12, pady=15)

        ctk.CTkLabel(u_card, text=f"👤 {self.user}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#FFFFFF").pack(anchor="w", padx=10, pady=(8, 2))
        _, sub_status = self.db.check_subscription(self.user)
        self.lbl_sub_info = ctk.CTkLabel(u_card, text=f"Статус: {sub_status}", font=ctk.CTkFont(size=10),
                                         text_color="#4EFEAA")
        self.lbl_sub_info.pack(anchor="w", padx=10, pady=(0, 4))

        btn_logout = ctk.CTkButton(u_card, text="Выйти из аккаунта", font=ctk.CTkFont(size=10), height=24,
                                   fg_color="#3F3F46", hover_color="#52525B", command=self.logout_account)
        btn_logout.pack(fill="x", padx=10, pady=(0, 8))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.views = {}
        self.build_view_main()
        self.build_view_ai()
        self.build_view_shop()
        self.build_view_settings()
        self.build_view_support()
        if self.db.is_developer(self.user):
            self.build_view_admin()

        self.tab("main")

    def logout_account(self):
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти из аккаунта?"):
            if self.engine.is_running:
                self.engine.stop()
            self.user = None
            ToastNotification(self, "Вы успешно вышли из аккаунта")
            self.render_auth()

    def tab(self, name):
        for v in self.views.values():
            v.pack_forget()

        nav_buttons = [self.b_main, self.b_ai, self.b_shop, self.b_set, self.b_support]
        if self.b_admin:
            nav_buttons.append(self.b_admin)

        for b in nav_buttons:
            b.configure(fg_color="transparent", text_color="#A1A1AA")

        if name == "main":
            self.b_main.configure(fg_color="#27272A", text_color="#FFFFFF")
        elif name == "ai":
            self.b_ai.configure(fg_color="#27272A", text_color="#FFFFFF")
        elif name == "shop":
            self.b_shop.configure(fg_color="#27272A", text_color="#FFFFFF")
        elif name == "settings":
            self.b_set.configure(fg_color="#27272A", text_color="#FFFFFF")
        elif name == "support":
            self.b_support.configure(fg_color="#27272A", text_color="#FFFFFF")
            self.refresh_tickets_list()
        elif name == "admin" and self.b_admin:
            self.b_admin.configure(fg_color="#27272A", text_color="#F59E0B")
            self.refresh_admin_dashboard()

        self.views[name].pack(fill="both", expand=True)

    # 1. Главная
    def build_view_main(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["main"] = v

        ctk.CTkLabel(v, text="Управление Автокликером", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w",
                                                                                                       pady=(0, 15))

        st_card = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        st_card.pack(fill="x", pady=10)

        self.lbl_st = ctk.CTkLabel(st_card, text="СТАТУС: ВЫКЛЮЧЕН", font=ctk.CTkFont(size=15, weight="bold"),
                                   text_color="#E11D48")
        self.lbl_st.pack(pady=22)

        self.btn_toggle = ctk.CTkButton(v, text="ЗАПУСТИТЬ ДВИЖОК", font=ctk.CTkFont(size=13, weight="bold"), height=46,
                                        fg_color="#E11D48", hover_color="#BE123C", command=self.toggle_bot)
        self.btn_toggle.pack(fill="x", pady=10)

        box = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        box.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(box,
                     text="Быстрая инструкция:\n1. Нажмите «Запустить движок».\n2. Перейдите в окно GTA V / Majestic.\n3. Нажмите F5 для активации захвата и авторыбалки.",
                     font=ctk.CTkFont(size=12), text_color="#71717A", justify="left").pack(anchor="w", padx=15, pady=15)

    # 2. ИИ & Обучение на Фото/Видео
    def build_view_ai(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["ai"] = v

        ctk.CTkLabel(v, text="Обучение ИИ по Фото и Видео Датасетам", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(0, 15))

        ds_box = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        ds_box.pack(fill="x", pady=5)

        ctk.CTkLabel(ds_box, text="Путь к директории с фото/видео:", font=ctk.CTkFont(size=12)).pack(anchor="w",
                                                                                                     padx=15,
                                                                                                     pady=(12, 5))

        path_frame = ctk.CTkFrame(ds_box, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.ent_dataset_path = ctk.CTkEntry(path_frame, placeholder_text="Выберите папку с датасетом...",
                                             fg_color="#27272A")
        self.ent_dataset_path.insert(0, DATASET_DIR)
        self.ent_dataset_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(path_frame, text="Обзор...", width=90, fg_color="#27272A", command=self.browse_dataset_dir).pack(
            side="right")

        self.btn_train_ds = ctk.CTkButton(ds_box, text="ЗАПУСТИТЬ ОБУЧЕНИЕ ПО ДАТАСЕТУ",
                                          font=ctk.CTkFont(size=12, weight="bold"), fg_color="#E11D48",
                                          hover_color="#BE123C", command=self.start_dataset_training)
        self.btn_train_ds.pack(anchor="w", padx=15, pady=(5, 15))

        self.lbl_train_status = ctk.CTkLabel(ds_box, text="Статус: Ожидание действия", font=ctk.CTkFont(size=11),
                                             text_color="#A1A1AA")
        self.lbl_train_status.pack(anchor="w", padx=15, pady=(0, 12))

        info = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        info.pack(fill="x", pady=10)

        self.lbl_mem = ctk.CTkLabel(info, text="Replay Buffer: 0 / 10000", font=ctk.CTkFont(size=12))
        self.lbl_mem.pack(anchor="w", padx=15, pady=(10, 2))

        self.lbl_loss = ctk.CTkLabel(info, text="Текущий Loss: 0.0000", font=ctk.CTkFont(size=12))
        self.lbl_loss.pack(anchor="w", padx=15, pady=(0, 2))

        self.lbl_eps = ctk.CTkLabel(info, text="Epsilon (Исследование): 1.00", font=ctk.CTkFont(size=12))
        self.lbl_eps.pack(anchor="w", padx=15, pady=(0, 10))

        grid = ctk.CTkFrame(v, fg_color="transparent")
        grid.pack(fill="x", pady=10)

        ctk.CTkButton(grid, text="Сохранить веса (.pth)", fg_color="#27272A", command=self.save_weights).pack(
            side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(grid, text="Загрузить веса (.pth)", fg_color="#27272A", command=self.load_weights).pack(
            side="right", expand=True, fill="x", padx=(5, 0))

    def browse_dataset_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.ent_dataset_path.delete(0, 'end')
            self.ent_dataset_path.insert(0, d)

    def start_dataset_training(self):
        if self.engine.is_running:
            messagebox.showerror("Ошибка", "Нельзя запустить обучение во время работы авторыбалки!")
            return

        path = self.ent_dataset_path.get().strip()
        self.btn_train_ds.configure(state="disabled")
        self.lbl_train_status.configure(text="Статус: Обучение запущено...")

        def _status_update(txt):
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self.lbl_train_status.configure(text=f"Статус: {txt}") if self.winfo_exists() else None)
            except Exception:
                pass

        def _on_done(ok, msg):
            def _ui():
                try:
                    if self.winfo_exists():
                        self.btn_train_ds.configure(state="normal")
                        self.lbl_train_status.configure(text=f"Статус: {msg}")
                        if ok:
                            messagebox.showinfo("Успех", msg)
                        else:
                            messagebox.showerror("Ошибка", msg)
                except Exception:
                    pass

            try:
                if self.winfo_exists():
                    self.after(0, _ui)
            except Exception:
                pass

        self.engine.train_dataset_async(path, _status_update, _on_done)

    # 3. Подписка
    def build_view_shop(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["shop"] = v

        ctk.CTkLabel(v, text="Активация Ключей / Промокодов", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w",
                                                                                                             pady=(0,
                                                                                                                   15))

        card = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        card.pack(fill="x", pady=5)

        ctk.CTkLabel(card, text="Введите промокод или ключ подписки:", font=ctk.CTkFont(size=12)).pack(anchor="w",
                                                                                                       padx=15,
                                                                                                       pady=(12, 5))

        self.ent_promo = ctk.CTkEntry(card, placeholder_text="Например: MAJESTIC30", width=300, fg_color="#27272A")
        self.ent_promo.pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkButton(card, text="Активировать Ключ", fg_color="#E11D48", hover_color="#BE123C",
                      command=self.apply_promo).pack(anchor="w", padx=15, pady=(0, 15))

    # 4. Настройки
    def build_view_settings(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["settings"] = v

        ctk.CTkLabel(v, text="Настройки Управления и Зоны Захвата", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(0, 15))

        card = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        card.pack(fill="x", pady=5)

        ctk.CTkLabel(card, text="Горячая клавиша Старт/Пауза:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=(10, 2))
        self.ent_hk = ctk.CTkEntry(card, width=120, fg_color="#27272A")
        self.ent_hk.insert(0, self.engine.hotkey)
        self.ent_hk.pack(anchor="w", padx=15, pady=(0, 10))

        coord_frame = ctk.CTkFrame(card, fg_color="transparent")
        coord_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(coord_frame, text="Координаты зоны захвата (0.0 - 1.0):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))
        
        ctk.CTkLabel(coord_frame, text="Смещение X:", font=ctk.CTkFont(size=11)).grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.ent_scale_x = ctk.CTkEntry(coord_frame, width=70, fg_color="#27272A")
        self.ent_scale_x.insert(0, str(self.engine.scale_x))
        self.ent_scale_x.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=4)
        
        ctk.CTkLabel(coord_frame, text="Смещение Y:", font=ctk.CTkFont(size=11)).grid(row=1, column=2, sticky="w", padx=(0, 10))
        self.ent_scale_y = ctk.CTkEntry(coord_frame, width=70, fg_color="#27272A")
        self.ent_scale_y.insert(0, str(self.engine.scale_y))
        self.ent_scale_y.grid(row=1, column=3, sticky="w", padx=(0, 20), pady=4)
        
        ctk.CTkLabel(coord_frame, text="Ширина W:", font=ctk.CTkFont(size=11)).grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.ent_scale_w = ctk.CTkEntry(coord_frame, width=70, fg_color="#27272A")
        self.ent_scale_w.insert(0, str(self.engine.scale_w))
        self.ent_scale_w.grid(row=2, column=1, sticky="w", padx=(0, 20), pady=4)
        
        ctk.CTkLabel(coord_frame, text="Высота H:", font=ctk.CTkFont(size=11)).grid(row=2, column=2, sticky="w", padx=(0, 10))
        self.ent_scale_h = ctk.CTkEntry(coord_frame, width=70, fg_color="#27272A")
        self.ent_scale_h.insert(0, str(self.engine.scale_h))
        self.ent_scale_h.grid(row=2, column=3, sticky="w", padx=(0, 20), pady=4)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(15, 15))

        btn_save = ctk.CTkButton(btn_frame, text="Применить настройки", fg_color="#27272A", width=160, command=self.apply_settings)
        btn_save.pack(side="left", padx=(0, 10))

        btn_debug = ctk.CTkButton(btn_frame, text="📸 Проверить захват (Скриншот)", fg_color="#E11D48", hover_color="#BE123C", width=220, command=self.take_debug_screenshot)
        btn_debug.pack(side="left")

    # 5. Служба поддержки
    def build_view_support(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["support"] = v

        left_pane = ctk.CTkFrame(v, width=240, fg_color="#18181B", corner_radius=10)
        left_pane.pack(side="left", fill="both", padx=(0, 10))
        left_pane.pack_propagate(False)

        right_pane = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        right_pane.pack(side="right", fill="both", expand=True)
        self.support_detail_frame = right_pane

        ctk.CTkLabel(left_pane, text="💬 Обращения", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 5))

        self.support_list_frame = ctk.CTkScrollableFrame(left_pane, fg_color="transparent")
        self.support_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        btn_new_ticket = ctk.CTkButton(left_pane, text="➕ Создать тикет", font=ctk.CTkFont(size=12, weight="bold"),
                                       fg_color="#E11D48", hover_color="#BE123C", command=self.show_create_ticket_view)
        btn_new_ticket.pack(fill="x", padx=12, pady=12)

        self.show_support_placeholder()

    def show_support_placeholder(self):
        self.clear_frame(self.support_detail_frame)
        self.selected_ticket_id = None
        
        placeholder = ctk.CTkLabel(self.support_detail_frame, 
                                   text="Выберите тикет из списка слева\nили создайте новый запрос.", 
                                   font=ctk.CTkFont(size=13), text_color="#71717A")
        placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def refresh_tickets_list(self):
        if not self.user:
            return
        
        self.clear_frame(self.support_list_frame)
        
        is_dev = self.db.is_developer(self.user)
        tickets = self.support_manager.get_user_tickets(self.user, is_dev=is_dev)
        
        if not tickets:
            no_ticks = ctk.CTkLabel(self.support_list_frame, text="Нет тикетов", font=ctk.CTkFont(size=12), text_color="#71717A")
            no_ticks.pack(pady=20)
            return

        for t in tickets:
            card = ctk.CTkFrame(self.support_list_frame, fg_color="#27272A", corner_radius=6, cursor="hand2")
            card.pack(fill="x", pady=4, padx=2)
            
            tid = t["ticket_id"]
            card.bind("<Button-1>", lambda event, i=tid: self.show_ticket_detail(i))
            card.columnconfigure(0, weight=1)
            
            title_text = t["title"]
            if len(title_text) > 22:
                title_text = title_text[:20] + "..."
            
            lbl_title = ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), anchor="w", text_color="#FFFFFF")
            lbl_title.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")
            lbl_title.bind("<Button-1>", lambda event, i=tid: self.show_ticket_detail(i))
            
            lbl_info = ctk.CTkLabel(card, text=f"#{tid} | {t['category']}", font=ctk.CTkFont(size=10), text_color="#A1A1AA", anchor="w")
            lbl_info.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="w")
            lbl_info.bind("<Button-1>", lambda event, i=tid: self.show_ticket_detail(i))

            status_colors = {
                "Открыт": "#FF9900",
                "В процессе": "#0099FF",
                "Решен": "#4EFEAA",
                "Закрыт": "#71717A"
            }
            color = status_colors.get(t["status"], "#FFFFFF")
            
            lbl_status = ctk.CTkLabel(card, text=t["status"], font=ctk.CTkFont(size=10, weight="bold"), text_color=color, anchor="e")
            lbl_status.grid(row=0, rowspan=2, column=1, padx=8, pady=6, sticky="e")
            lbl_status.bind("<Button-1>", lambda event, i=tid: self.show_ticket_detail(i))

    def show_create_ticket_view(self):
        self.clear_frame(self.support_detail_frame)
        self.selected_ticket_id = None
        
        form = ctk.CTkFrame(self.support_detail_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form, text="Создание нового обращения", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(form, text="Тема обращения:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 2))
        self.ent_ticket_title = ctk.CTkEntry(form, placeholder_text="Кратко опишите суть...", fg_color="#27272A", height=32)
        self.ent_ticket_title.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form, text="Категория:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 2))
        self.opt_ticket_category = ctk.CTkOptionMenu(form, values=["Баг / Ошибка", "Предложение", "Вопрос по подписке", "Другое"], fg_color="#27272A", button_color="#18181B")
        self.opt_ticket_category.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form, text="Подробное описание:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 2))
        self.txt_ticket_desc = ctk.CTkTextbox(form, fg_color="#27272A", height=150)
        self.txt_ticket_desc.pack(fill="both", expand=True, pady=(0, 15))
        
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Отмена", fg_color="#27272A", width=100, command=self.show_support_placeholder)
        btn_cancel.pack(side="left", padx=(0, 10))
        
        btn_submit = ctk.CTkButton(btn_frame, text="Отправить", fg_color="#E11D48", hover_color="#BE123C", width=120, command=self.submit_new_ticket)
        btn_submit.pack(side="right")

    def submit_new_ticket(self):
        title = self.ent_ticket_title.get().strip()
        category = self.opt_ticket_category.get()
        description = self.txt_ticket_desc.get("1.0", "end-1c").strip()
        
        if not title or not description:
            messagebox.showerror("Ошибка", "Заполните все поля тикета!")
            return
            
        ok, res = self.support_manager.create_ticket(self.user, title, description, category)
        if ok:
            ToastNotification(self, f"Тикет #{res} успешно отправлен!")
            self.refresh_tickets_list()
            self.show_ticket_detail(res)
        else:
            messagebox.showerror("Ошибка", res)

    def show_ticket_detail(self, ticket_id):
        self.selected_ticket_id = ticket_id
        t = self.support_manager.get_ticket(ticket_id)
        if not t:
            self.show_support_placeholder()
            return
            
        self.clear_frame(self.support_detail_frame)
        
        details = ctk.CTkFrame(self.support_detail_frame, fg_color="transparent")
        details.pack(fill="both", expand=True, padx=15, pady=15)
        
        header = ctk.CTkFrame(details, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(title_frame, text=f"Тикет #{t['ticket_id']}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w", text_color="#A1A1AA").pack(anchor="w")
        
        lbl_t_title = ctk.CTkLabel(title_frame, text=t["title"], font=ctk.CTkFont(size=16, weight="bold"), anchor="w", justify="left")
        lbl_t_title.pack(anchor="w", pady=(2, 2))
        
        is_dev = self.db.is_developer(self.user)
        
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", fill="y", padx=(10, 0))
        
        if is_dev:
            ctk.CTkLabel(status_frame, text="Статус:", font=ctk.CTkFont(size=11), text_color="#71717A").pack(anchor="e")
            opt_status = ctk.CTkOptionMenu(status_frame, values=["Открыт", "В процессе", "Решен", "Закрыт"], 
                                           width=110, height=28, fg_color="#27272A", button_color="#18181B",
                                           command=lambda val, tid=ticket_id: self.change_ticket_status(tid, val))
            opt_status.set(t["status"])
            opt_status.pack(anchor="e", pady=2)
        else:
            status_colors = {
                "Открыт": "#FF9900",
                "В процессе": "#0099FF",
                "Решен": "#4EFEAA",
                "Закрыт": "#71717A"
            }
            color = status_colors.get(t["status"], "#FFFFFF")
            lbl_st_label = ctk.CTkLabel(status_frame, text=t["status"].upper(), font=ctk.CTkFont(size=12, weight="bold"), text_color=color, fg_color="#27272A", corner_radius=6, padx=8, pady=4)
            lbl_st_label.pack(anchor="e", pady=5)
            
        lbl_meta = ctk.CTkLabel(details, text=f"Создатель: {t['username']}  |  Категория: {t['category']}  |  Дата: {t['created_at']}", font=ctk.CTkFont(size=10), text_color="#71717A", anchor="w")
        lbl_meta.pack(anchor="w", pady=(0, 10))
        
        body = ctk.CTkFrame(details, fg_color="transparent")
        body.pack(fill="both", expand=True)
        
        desc_card = ctk.CTkFrame(body, fg_color="#27272A", corner_radius=8)
        desc_card.pack(fill="x", pady=(0, 10))
        
        desc_title = ctk.CTkLabel(desc_card, text="Описание проблемы:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A1A1AA")
        desc_title.pack(anchor="w", padx=10, pady=(6, 2))
        
        desc_text = ctk.CTkLabel(desc_card, text=t["description"], font=ctk.CTkFont(size=12), justify="left", wraplength=400, anchor="w")
        desc_text.pack(anchor="w", padx=10, pady=(0, 10))
        
        comments_lbl = ctk.CTkLabel(body, text="История обсуждения:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A1A1AA")
        comments_lbl.pack(anchor="w", pady=(5, 2))
        
        self.comments_frame = ctk.CTkScrollableFrame(body, fg_color="#121214", corner_radius=8, height=160)
        self.comments_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.populate_comments(t["comments"])
        
        comment_input_frame = ctk.CTkFrame(body, fg_color="transparent")
        comment_input_frame.pack(fill="x", side="bottom")
        
        self.txt_new_comment = ctk.CTkEntry(comment_input_frame, placeholder_text="Введите сообщение...", fg_color="#27272A", height=36)
        self.txt_new_comment.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.txt_new_comment.bind("<Return>", lambda event: self.submit_comment())
        
        btn_send_comment = ctk.CTkButton(comment_input_frame, text="Отправить", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#E11D48", hover_color="#BE123C", width=90, height=36, command=self.submit_comment)
        btn_send_comment.pack(side="right")

    def change_ticket_status(self, ticket_id, new_status):
        ok, msg = self.support_manager.update_status(ticket_id, new_status)
        if ok:
            self.refresh_tickets_list()
            self.show_ticket_detail(ticket_id)
        else:
            messagebox.showerror("Ошибка", msg)

    def populate_comments(self, comments):
        self.clear_frame(self.comments_frame)
        if not comments:
            no_comm = ctk.CTkLabel(self.comments_frame, text="Комментариев пока нет.", font=ctk.CTkFont(size=11), text_color="#71717A")
            no_comm.pack(pady=15)
            return
            
        for c in comments:
            is_c_dev = c.get("is_dev", False)
            bg = "#1E293B" if is_c_dev else "#27272A"
            
            comment_card = ctk.CTkFrame(self.comments_frame, fg_color=bg, corner_radius=6)
            comment_card.pack(fill="x", pady=4, padx=2)
            
            meta_frame = ctk.CTkFrame(comment_card, fg_color="transparent")
            meta_frame.pack(fill="x", padx=8, pady=(4, 2))
            
            author_text = c["author"]
            if is_c_dev:
                author_text += " [РАЗРАБОТЧИК]"
            
            lbl_author = ctk.CTkLabel(meta_frame, text=author_text, font=ctk.CTkFont(size=11, weight="bold"), 
                                      text_color="#60A5FA" if is_c_dev else "#4EFEAA", anchor="w")
            lbl_author.pack(side="left")
            
            lbl_time = ctk.CTkLabel(meta_frame, text=c["timestamp"], font=ctk.CTkFont(size=9), text_color="#71717A", anchor="e")
            lbl_time.pack(side="right")
            
            lbl_text = ctk.CTkLabel(comment_card, text=c["text"], font=ctk.CTkFont(size=11), justify="left", wraplength=350, anchor="w")
            lbl_text.pack(anchor="w", padx=8, pady=(0, 6))
            
        try:
            self.comments_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def submit_comment(self):
        if not self.selected_ticket_id:
            return
            
        text = self.txt_new_comment.get().strip()
        if not text:
            return
            
        is_dev = self.db.is_developer(self.user)
        
        ok, msg = self.support_manager.add_comment(self.selected_ticket_id, self.user, text, is_dev=is_dev)
        if ok:
            self.txt_new_comment.delete(0, 'end')
            t = self.support_manager.get_ticket(self.selected_ticket_id)
            if t:
                self.populate_comments(t["comments"])
        else:
            messagebox.showerror("Ошибка", msg)

    # 6. Админ-кабинет разработчика
    def build_view_admin(self):
        v = ctk.CTkFrame(self.container, fg_color="transparent")
        self.views["admin"] = v

        ctk.CTkLabel(v, text="👑 Кабинет разработчика", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F59E0B").pack(anchor="w", pady=(0, 15))

        stats_card = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        stats_card.pack(fill="x", pady=5)

        ctk.CTkLabel(stats_card, text="Системная статистика:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 5))
        
        self.lbl_admin_stats = ctk.CTkLabel(stats_card, text="Загрузка данных...", font=ctk.CTkFont(size=12), justify="left")
        self.lbl_admin_stats.pack(anchor="w", padx=15, pady=(0, 15))

        actions_card = ctk.CTkFrame(v, fg_color="#18181B", corner_radius=10)
        actions_card.pack(fill="x", pady=10)

        ctk.CTkLabel(actions_card, text="Быстрые действия:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 5))
        
        btn_refresh_admin = ctk.CTkButton(actions_card, text="Обновить статистику", fg_color="#27272A", width=180, command=self.refresh_admin_dashboard)
        btn_refresh_admin.pack(anchor="w", padx=15, pady=(0, 15))

    def refresh_admin_dashboard(self):
        if not self.db.is_developer(self.user):
            return
        
        # Получаем общую статистику из базы/системы
        try:
            tickets_all = self.support_manager.get_user_tickets(self.user, is_dev=True)
            open_ticks = len([t for t in tickets_all if t["status"] in ["Открыт", "В процессе"]])
            
            info_str = (
                f"• Текущий разработчик: {self.user}\n"
                f"• Всего тикетов в системе: {len(tickets_all)}\n"
                f"• Активных/Открытых тикетов: {open_ticks}\n"
                f"• Статус движка ИИ: {'Активен' if self.engine.is_running else 'Остановлен'}"
            )
            self.lbl_admin_stats.configure(text=info_str)
        except Exception as e:
            self.lbl_admin_stats.configure(text=f"Ошибка загрузки статистики: {str(e)}")

    # Хэндлеры UI
    def apply_promo(self):
        code = self.ent_promo.get()
        ok, msg = self.db.activate_promo(self.user, code)
        if ok:
            messagebox.showinfo("Успех", msg)
            _, sub_status = self.db.check_subscription(self.user)
            self.lbl_sub_info.configure(text=f"Статус: {sub_status}")
        else:
            messagebox.showerror("Ошибка", msg)

    def apply_settings(self):
        val = self.ent_hk.get().lower().strip()
        if val:
            self.engine.hotkey = val
            
        try:
            sx = float(self.ent_scale_x.get().strip())
            sy = float(self.ent_scale_y.get().strip())
            sw = float(self.ent_scale_w.get().strip())
            sh = float(self.ent_scale_h.get().strip())
            
            if not (0.0 <= sx <= 1.0 and 0.0 <= sy <= 1.0 and 0.0 <= sw <= 1.0 and 0.0 <= sh <= 1.0):
                raise ValueError("Коэффициенты должны быть в диапазоне от 0.0 до 1.0!")
                
            self.engine.scale_x = sx
            self.engine.scale_y = sy
            self.engine.scale_w = sw
            self.engine.scale_h = sh
            
            messagebox.showinfo("Успех", f"Настройки применены!\nКлавиша: {val.upper()}\nЗона: X={sx}, Y={sy}, W={sw}, H={sh}")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные настройки координат:\n{str(e)}")

    def take_debug_screenshot(self):
        ok, msg = self.engine.save_debug_screenshot()
        if ok:
            messagebox.showinfo("Проверка захвата", msg)
        else:
            messagebox.showerror("Ошибка проверки", msg)

    def save_weights(self):
        self.engine.agent.save()
        messagebox.showinfo("ИИ", "Веса успешно сохранены!")

    def load_weights(self):
        if self.engine.agent.load():
            messagebox.showinfo("ИИ", "Веса успешно загружены!")
        else:
            messagebox.showerror("Ошибка", "Файл весов не найден!")

    def update_engine_status(self, text, color):
        try:
            if self.winfo_exists():
                self.after(0, lambda: self.lbl_st.configure(text=f"СТАТУС: {text}", text_color=color) if self.winfo_exists() else None)
        except Exception:
            pass

    def update_engine_metrics(self, mem, loss, eps):
        try:
            if self.winfo_exists():
                self.after(0, lambda: self._sync_metrics(mem, loss, eps) if self.winfo_exists() else None)
        except Exception:
            pass

    def _sync_metrics(self, mem, loss, eps):
        try:
            if self.winfo_exists():
                self.lbl_mem.configure(text=f"Replay Buffer: {mem} / 10000")
                self.lbl_loss.configure(text=f"Текущий Loss: {loss:.5f}")
                self.lbl_eps.configure(text=f"Epsilon (Исследование): {eps:.2f}")
        except Exception:
            pass

    def toggle_bot(self):
        if getattr(self.engine, "is_training", False):
            messagebox.showerror("Ошибка", "Нельзя запустить авторыбалку, пока идет обучение датасета!")
            return

        if not self.engine.is_running:
            self.engine.start_thread(self.update_engine_status, self.update_engine_metrics)
            self.btn_toggle.configure(text="ОСТАНОВИТЬ ДВИЖОК", fg_color="#E11D48")
            self.update_engine_status(f"ОЖИДАНИЕ ({self.engine.hotkey.upper()} в игре)", "#E5C07B")
        else:
            self.engine.stop()
            self.btn_toggle.configure(text="ЗАПУСТИТЬ ДВИЖОК", fg_color="#E11D48")
            self.update_engine_status("ВЫКЛЮЧЕН", "#E11D48")

    def on_closing(self):
        is_training = getattr(self.engine, "is_training", False)
        if self.engine.is_running or is_training:
            msg = "Идет процесс обучения датасета." if is_training else "Движок бота запущен."
            if messagebox.askokcancel("Выход", f"{msg}\nВы действительно хотите закрыть программу?"):
                self.engine.stop()
                self.destroy()
        else:
            self.destroy()