import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users_db.json")
MODEL_FILE = os.path.join(BASE_DIR, "dqn_model.pth")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# Параметры захвата экрана (центр нижней части экрана под интерфейс рыбалки GTA V / Majestic)
DEFAULT_SCALE_X = 0.32
DEFAULT_SCALE_Y = 0.78
DEFAULT_SCALE_W = 0.36
DEFAULT_SCALE_H = 0.08

# HSV фильтры для поиска зеленой зоны шкалы и белого маркера
LOWER_GREEN = (35, 40, 40)
UPPER_GREEN = (90, 255, 255)

LOWER_WHITE = (0, 0, 180)
UPPER_WHITE = (180, 60, 255)

TRIAL_DAYS = 3
PROMO_CODES = {
    "MAJESTIC30": 30,
    "PROMO7": 7,
    "VIP365": 365
}

DEV_TEAM = ["admin", "Developer", "pogo"]