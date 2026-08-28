import os
import json
import hashlib
import binascii
import threading
from datetime import datetime, timedelta
from config import DB_FILE, TRIAL_DAYS, PROMO_CODES, DEV_TEAM


class DatabaseManager:
    def __init__(self):
        self.db_path = DB_FILE
        self.lock = threading.Lock()
        self.users = self._load_db()

    def _hash_password(self, password, salt=None):
        if not salt:
            salt = os.urandom(16)
        if isinstance(salt, str):
            salt = binascii.unhexlify(salt)
        # Укрепленный алгоритм PBKDF2-HMAC-SHA256
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return binascii.hexlify(salt).decode('ascii') + ":" + binascii.hexlify(pwdhash).decode('ascii')

    def _verify_password(self, stored_password, provided_password):
        try:
            salt_hex, stored_pwd_hex = stored_password.split(':')
            salt = binascii.unhexlify(salt_hex)
            pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return stored_pwd_hex == binascii.hexlify(pwdhash).decode('ascii')
        except Exception:
            return False

    def _load_db(self):
        with self.lock:
            forever_date = (datetime.now() + timedelta(days=36500)).strftime("%Y-%m-%d %H:%M:%S")
            if not os.path.exists(self.db_path):
                default_db = {}
                for dev in DEV_TEAM:
                    default_db[dev] = {
                        "password": self._hash_password("12345"),
                        "sub_until": forever_date,
                        "is_trial_used": True,
                        "is_dev": True
                    }
                self._save_raw(default_db)
                return default_db
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    self._ensure_devs(db)
                    return db
            except Exception:
                return {}

    def _ensure_devs(self, db):
        updated = False
        forever_date = (datetime.now() + timedelta(days=36500)).strftime("%Y-%m-%d %H:%M:%S")
        for dev in DEV_TEAM:
            if dev not in db:
                db[dev] = {
                    "password": self._hash_password("12345"),
                    "sub_until": forever_date,
                    "is_trial_used": True,
                    "is_dev": True
                }
                updated = True
            else:
                db[dev]["sub_until"] = forever_date
                db[dev]["is_dev"] = True
                updated = True
        if updated:
            self._save_raw(db)

    def _save_raw(self, data):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _save(self):
        with self.lock:
            self._save_raw(self.users)

    def register(self, username, password):
        username = username.strip()
        if not username or not password:
            return False, "Заполните все поля!"
        if len(password) < 4:
            return False, "Пароль должен быть не менее 4 символов!"

        with self.lock:
            if username in self.users:
                return False, "Пользователь уже существует!"

            if username in DEV_TEAM:
                sub_time = datetime.now() + timedelta(days=36500)
                is_dev = True
                msg = f"Приветствуем разработчика {username}! Активирована вечная подписка."
            else:
                sub_time = datetime.now() + timedelta(days=TRIAL_DAYS)
                is_dev = False
                msg = f"Регистрация успешна! Активирован триал на {TRIAL_DAYS} дня(ей)."

            self.users[username] = {
                "password": self._hash_password(password),
                "sub_until": sub_time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_trial_used": True,
                "is_dev": is_dev
            }
            self._save_raw(self.users)
            return True, msg

    def login(self, username, password):
        username = username.strip()
        with self.lock:
            if username not in self.users:
                return False, "Пользователь не найден!"
            if not self._verify_password(self.users[username]["password"], password):
                return False, "Неверный пароль!"
        return True, "Успешная авторизация!"

    def check_subscription(self, username):
        with self.lock:
            if username not in self.users:
                return False, "Пользователь не найден"

            if username in DEV_TEAM or self.users[username].get("is_dev", False):
                return True, "Вечная подписка (Dev Team)"

            sub_str = self.users[username].get("sub_until")
            if not sub_str:
                return False, "Подписка не найдена"

            expire_date = datetime.strptime(sub_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < expire_date:
                days_left = (expire_date - datetime.now()).days
                return True, f"Активна (осталось {days_left} дн.)"
            return False, "Срок подписки истек!"

    def activate_promo(self, username, promo_code):
        with self.lock:
            if username in DEV_TEAM or self.users.get(username, {}).get("is_dev", False):
                return True, "У вас уже вечная подписка разработчика!"

            promo_code = promo_code.strip().upper()
            if promo_code not in PROMO_CODES:
                return False, "Неверный промокод/ключ!"

            days_to_add = PROMO_CODES[promo_code]
            user_data = self.users.get(username)
            if not user_data:
                return False, "Пользователь не найден"

            current_sub = datetime.strptime(user_data["sub_until"], "%Y-%m-%d %H:%M:%S")
            start_date = max(datetime.now(), current_sub)
            new_sub = start_date + timedelta(days=days_to_add)

            user_data["sub_until"] = new_sub.strftime("%Y-%m-%d %H:%M:%S")
            self._save_raw(self.users)
            return True, f"Подписка продлена на {days_to_add} дней!"

    def is_developer(self, username):
        if not username:
            return False
        with self.lock:
            if username not in self.users:
                return False
            return username in DEV_TEAM or self.users[username].get("is_dev", False)