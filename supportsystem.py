import os
import json
import uuid
import threading
from datetime import datetime
from config import BASE_DIR

TICKETS_FILE = os.path.join(BASE_DIR, "tickets_db.json")


class SupportManager:
    def __init__(self):
        self.db_path = TICKETS_FILE
        self.lock = threading.Lock()
        self.tickets = self._load_db()

    def _load_db(self):
        with self.lock:
            if not os.path.exists(self.db_path):
                self._save_raw({})
                return {}
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}

    def _save_raw(self, data):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def _save(self):
        with self.lock:
            self._save_raw(self.tickets)

    def create_ticket(self, username, title, description, category):
        title = title.strip()
        description = description.strip()
        category = category.strip()
        
        if not title or not description or not category:
            return False, "Все поля должны быть заполнены!"

        ticket_id = str(uuid.uuid4())[:8].upper()
        ticket = {
            "ticket_id": ticket_id,
            "username": username,
            "title": title,
            "description": description,
            "category": category,
            "status": "Открыт",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "comments": []
        }

        with self.lock:
            self.tickets[ticket_id] = ticket
            self._save_raw(self.tickets)
        return True, ticket_id

    def get_user_tickets(self, username, is_dev=False):
        with self.lock:
            if is_dev:
                # Developers see all tickets sorted by date
                ticks = list(self.tickets.values())
            else:
                ticks = [t for t in self.tickets.values() if t["username"] == username]
            
            # Sort by created_at descending
            return sorted(ticks, key=lambda x: x["created_at"], reverse=True)

    def get_ticket(self, ticket_id):
        with self.lock:
            return self.tickets.get(ticket_id)

    def add_comment(self, ticket_id, author, text, is_dev=False):
        text = text.strip()
        if not text:
            return False, "Комментарий не может быть пустым!"

        with self.lock:
            if ticket_id not in self.tickets:
                return False, "Тикет не найден!"

            comment = {
                "author": author,
                "text": text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_dev": is_dev
            }
            self.tickets[ticket_id]["comments"].append(comment)
            self._save_raw(self.tickets)
        return True, "Комментарий успешно добавлен!"

    def update_status(self, ticket_id, new_status):
        with self.lock:
            if ticket_id not in self.tickets:
                return False, "Тикет не найден!"
            
            self.tickets[ticket_id]["status"] = new_status
            self._save_raw(self.tickets)
        return True, "Статус тикета успешно обновлен!"
