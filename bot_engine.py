import time
import random
import threading
import cv2
import numpy as np
from mss import MSS
import keyboard
import win32gui
import ctypes

from config import DEFAULT_SCALE_X, DEFAULT_SCALE_Y, DEFAULT_SCALE_W, DEFAULT_SCALE_H, LOWER_GREEN, UPPER_GREEN, \
    LOWER_WHITE, UPPER_WHITE
from ai_model import DQNAgent

# --- Полезный функционал из GitHub кода: Прямой ввод SendInput для обхода хуков игры ---
SendInput = ctypes.windll.user32.SendInput

# Сканкоды клавиш (Scancodes)
SCAN_A = 0x1E
SCAN_D = 0x20
SCAN_SPACE = 0x39
SCAN_E = 0x12

PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def _send_key_state(scancode, flag):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scancode, flag, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def press_direct_key(scancode):
    _send_key_state(scancode, 0x0008)  # Нажатие (KEYEVENTF_SCANCODE)


def release_direct_key(scancode):
    _send_key_state(scancode, 0x0008 | 0x0002)  # Отпускание


# -----------------------------------------------------------------------------------------

def find_game_window():
    titles = ["Grand Theft Auto V", "Majestic RP", "GTA5", "RAGE Multiplayer", "RAGEMP"]
    for title in titles:
        hwnd = win32gui.FindWindow(None, title)
        if not hwnd:
            found_hwnds = []

            def enum_callback(h, extra):
                if win32gui.IsWindowVisible(h):
                    txt = win32gui.GetWindowText(h)
                    if title.lower() in txt.lower():
                        extra.append(h)

            win32gui.EnumWindows(enum_callback, found_hwnds)
            if found_hwnds:
                hwnd = found_hwnds[0]

        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
            if w > 100 and h > 100:
                return {"found": True, "x": x, "y": y, "w": w, "h": h}
    return {"found": False}


class FishingEngine:
    def __init__(self):
        self.is_running = False
        self.is_active = False
        self.is_training = False
        self.hotkey = "f5"
        self.agent = DQNAgent()
        self.agent.load()

        self.scale_x = DEFAULT_SCALE_X
        self.scale_y = DEFAULT_SCALE_Y
        self.scale_w = DEFAULT_SCALE_W
        self.scale_h = DEFAULT_SCALE_H

    def tap_key(self, scancode, duration=0.04):
        press_direct_key(scancode)
        time.sleep(random.uniform(duration, duration + 0.02))
        release_direct_key(scancode)

    def process_frame(self, frame):
        if frame is None or frame.size == 0:
            return 0.0, False, False

        bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR) if frame.shape[2] == 4 else frame
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        mask_g = cv2.inRange(hsv, np.array(LOWER_GREEN), np.array(UPPER_GREEN))
        mask_w = cv2.inRange(hsv, np.array(LOWER_WHITE), np.array(UPPER_WHITE))

        g_pts = np.column_stack(np.where(mask_g > 0))
        w_pts = np.column_stack(np.where(mask_w > 0))

        if len(g_pts) > 5 and len(w_pts) > 0:
            g_min_x = np.min(g_pts[:, 1])
            g_max_x = np.max(g_pts[:, 1])
            g_center = np.mean(g_pts[:, 1])
            
            w_center = np.mean(w_pts[:, 1])
            width = frame.shape[1]

            distance = (w_center - g_center) / width
            # Безопасная проверка с погрешностью ±5 пикселей во избежание пропусков из-за дребезга маски
            in_zone = (g_min_x - 5) <= w_center <= (g_max_x + 5)
            return distance, in_zone, True

        return 0.0, False, False

    def start_thread(self, status_cb, metrics_cb):
        self.is_running = True
        threading.Thread(target=self._main_loop, args=(status_cb, metrics_cb), daemon=True).start()

    def train_dataset_async(self, path, status_cb, done_cb):
        self.is_training = True
        def _train_job():
            try:
                ok, msg = self.agent.train_from_dataset(path, status_cb)
            except Exception as e:
                ok, msg = False, str(e)
            finally:
                self.is_training = False
            done_cb(ok, msg)

        threading.Thread(target=_train_job, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.is_active = False

    def save_debug_screenshot(self):
        win = find_game_window()
        if not win["found"]:
            return False, "Окно игры не найдено!"
            
        with MSS() as sct:
            game_rect = {
                "left": win["x"],
                "top": win["y"],
                "width": win["w"],
                "height": win["h"]
            }
            try:
                full_img = np.array(sct.grab(game_rect))
            except Exception as e:
                return False, f"Ошибка захвата: {str(e)}"
                
            if full_img.shape[2] == 4:
                full_img = cv2.cvtColor(full_img, cv2.COLOR_BGRA2BGR)
                
            zone_x = int(win["w"] * self.scale_x)
            zone_y = int(win["h"] * self.scale_y)
            zone_w = max(20, int(win["w"] * self.scale_w))
            zone_h = max(10, int(win["h"] * self.scale_h))
            
            cropped = full_img[zone_y:zone_y+zone_h, zone_x:zone_x+zone_w]
            
            cv2.rectangle(full_img, (zone_x, zone_y), (zone_x + zone_w, zone_y + zone_h), (0, 0, 255), 2)
            
            try:
                cv2.imwrite("debug_game_window.png", full_img)
                cv2.imwrite("debug_cropped_zone.png", cropped)
                return True, "Скрины сохранены (debug_game_window.png и debug_cropped_zone.png)!"
            except Exception as e:
                return False, f"Ошибка сохранения: {str(e)}"

    def _main_loop(self, status_cb, metrics_cb):
        last_hk_state = False
        with MSS() as sct:
            while self.is_running:
                try:
                    hk_pressed = keyboard.is_pressed(self.hotkey)
                    if hk_pressed and not last_hk_state:
                        self.is_active = not self.is_active
                        st_text = "АКТИВЕН" if self.is_active else f"ПАУЗА ({self.hotkey.upper()})"
                        st_color = "#4EFEAA" if self.is_active else "#E5C07B"
                        status_cb(st_text, st_color)
                    last_hk_state = hk_pressed
                except Exception:
                    pass

                if not self.is_active:
                    time.sleep(0.05)
                    continue

                win = find_game_window()
                if not win["found"]:
                    status_cb("ОКНО ИГРЫ НЕ НАЙДЕНО!", "#FF334B")
                    time.sleep(1.0)
                    continue

                zone = {
                    "left": int(win["x"] + win["w"] * self.scale_x),
                    "top": int(win["y"] + win["h"] * self.scale_y),
                    "width": max(20, int(win["w"] * self.scale_w)),
                    "height": max(10, int(win["h"] * self.scale_h))
                }

                status_cb("Заброс удочки (E)...", "#4EFEAA")
                self.tap_key(SCAN_E, 0.05)
                
                # Check running flag during sleep
                for _ in range(30):
                    if not self.is_running or not self.is_active:
                        break
                    time.sleep(random.uniform(0.04, 0.06))

                t_start = time.time()
                prev_dist = 0.0
                hooked = False

                while time.time() - t_start < 12.0:
                    if not self.is_active or not self.is_running:
                        break

                    try:
                        raw_img = np.array(sct.grab(zone))
                    except Exception:
                        break

                    if raw_img is not None and raw_img.size > 0:
                        if np.max(raw_img) <= 5:
                            status_cb("ЧЕРНЫЙ ЭКРАН (Оконный режим!)", "#FF334B")
                            time.sleep(1.0)
                            break

                    dist, in_zone, found = self.process_frame(raw_img)

                    if found:
                        speed = dist - prev_dist
                        prev_dist = dist
                        state = [dist, speed, 1.0 if in_zone else 0.0, 1.0]

                        action = self.agent.select_action(state)

                        # Fail-safe mode: Only press Space if actually in the green zone.
                        # This prevents early/late failure due to random DQN exploration (epsilon).
                        if in_zone:
                            self.tap_key(SCAN_SPACE, 0.04)
                            self.agent.store_transition(state, 1, 10.0, [dist, 0.0, 0.0, 0.0], True)
                            status_cb("ПОДСЕЧКА!", "#4EFEAA")
                            hooked = True
                            break
                        elif action == 1:
                            # DQN agent chose to press prematurely, record the negative reward
                            # but do NOT press the key in game to avoid failing the minigame.
                            self.agent.store_transition(state, action, -5.0, [dist, speed, 0.0, 1.0], False)

                    time.sleep(0.005)

                if not self.is_running:
                    break

                loss = self.agent.train_step()
                metrics_cb(len(self.agent.memory), loss, self.agent.epsilon)

                if hooked:
                    time.sleep(0.5)
                    reel_t = time.time()
                    while time.time() - reel_t < 6.0:
                        if not self.is_active or not self.is_running:
                            break
                        self.tap_key(SCAN_A, 0.06)
                        time.sleep(0.08)
                        self.tap_key(SCAN_D, 0.06)
                        time.sleep(0.09)

                if not self.is_running:
                    break
                
                # Check running flag during final sleep
                for _ in range(50):
                    if not self.is_running or not self.is_active:
                        break
                    time.sleep(random.uniform(0.04, 0.06))