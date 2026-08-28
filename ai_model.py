import os
import random
import cv2
import numpy as np
from collections import deque
import torch
import torch.nn as nn
import torch.optim as optim
from config import MODEL_FILE, LOWER_GREEN, UPPER_GREEN, LOWER_WHITE, UPPER_WHITE


class DeepFishingNetwork(nn.Module):
    def __init__(self, state_dim=4, action_dim=2):
        super(DeepFishingNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )

    def forward(self, x):
        if x.size(0) == 1:
            self.net.eval()
            out = self.net(x)
            self.net.train()
            return out
        return self.net(x)


class DQNAgent:
    def __init__(self, state_dim=4, action_dim=2):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.policy_net = DeepFishingNetwork(state_dim, action_dim).to(self.device)
        self.target_net = DeepFishingNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.lr = 0.001
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.lr)
        self.memory = deque(maxlen=10000)

        self.batch_size = 64
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995

    def select_action(self, state, eval_mode=False):
        """Выбор действия: случайно (исследование) или через нейросеть (эксплуатация)"""
        if not eval_mode and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        self.policy_net.eval()
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_t)
            return torch.argmax(q_values).item()

    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return 0.0

        self.policy_net.train()
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states_t = torch.FloatTensor(np.array(states)).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)

        current_q = self.policy_net(states_t).gather(1, actions_t).squeeze(1)
        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(1)[0]
            target_q = rewards_t + (1 - dones_t) * self.gamma * next_q

        loss = nn.MSELoss()(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return float(loss.item())

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, path=MODEL_FILE):
        torch.save(self.policy_net.state_dict(), path)

    def load(self, path=MODEL_FILE):
        if os.path.exists(path):
            try:
                self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
                self.update_target_network()
                return True
            except Exception:
                return False
        return False

    def get_state_and_reward(self, frame, prev_dist=0.0):
        """Анализирует текущий кадр из игры, формирует вектор состояния и рассчитывает награду"""
        dist, in_zone, found = self._parse_frame(frame)
        if not found:
            return None, 0.0, False, 0.0

        speed = dist - prev_dist
        # Состояние: [дистанция до центра, скорость изменения, флаг нахождения в зоне (1/0), флаг успешного распознавания]
        state = [dist, speed, 1.0 if in_zone else 0.0, 1.0]
        
        # Награда: поощряем нахождение белого маркера внутри зеленой зоны, штрафуем за вылет
        if in_zone:
            reward = 10.0
        else:
            reward = -5.0 - abs(dist) * 10  # чем дальше вылетел, тем сильнее штраф

        return state, reward, in_zone, dist

    def train_from_dataset(self, dataset_path, progress_cb=None):
        if not os.path.exists(dataset_path):
            return False, "Указанная директория не существует!"

        valid_exts_img = ('.png', '.jpg', '.jpeg', '.bmp')
        valid_exts_vid = ('.mp4', '.avi', '.mov', '.mkv')

        files = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path)]
        img_files = [f for f in files if f.lower().endswith(valid_exts_img)]
        vid_files = [f for f in files if f.lower().endswith(valid_exts_vid)]

        if not img_files and not vid_files:
            return False, "В папке не найдены файлы фото/видео!"

        processed_frames = 0
        prev_dist = 0.0

        for img_path in img_files:
            frame = cv2.imread(img_path)
            if frame is None:
                continue
            state, reward, in_zone, dist = self.get_state_and_reward(frame, prev_dist)
            if state is not None:
                prev_dist = dist
                action = 1 if in_zone else 0
                self.store_transition(state, action, reward, [dist, 0.0, 0.0, 0.0], True)
                processed_frames += 1

        for vid_path in vid_files:
            cap = cv2.VideoCapture(vid_path)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                state, reward, in_zone, dist = self.get_state_and_reward(frame, prev_dist)
                if state is not None:
                    prev_dist = dist
                    action = 1 if in_zone else 0
                    self.store_transition(state, action, reward, [dist, 0.0, 0.0, 0.0], True)
                    processed_frames += 1

                if processed_frames % 20 == 0 and progress_cb:
                    progress_cb(f"Обработано кадров: {processed_frames}")
            cap.release()

        total_loss = 0.0
        epochs = min(50, max(5, len(self.memory) // self.batch_size))
        for _ in range(epochs):
            loss = self.train_step()
            total_loss += loss

        self.update_target_network()
        self.save()

        avg_loss = total_loss / max(1, epochs)
        return True, f"Обучение завершено! Обработано кадров: {processed_frames}. Loss: {avg_loss:.5f}"

    def _parse_frame(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_g = cv2.inRange(hsv, np.array(LOWER_GREEN), np.array(UPPER_GREEN))
        mask_w = cv2.inRange(hsv, np.array(LOWER_WHITE), np.array(UPPER_WHITE))

        g_pts = np.column_stack(np.where(mask_g > 0))
        w_pts = np.column_stack(np.where(mask_w > 0))

        if len(g_pts) > 5 and len(w_pts) > 2:
            g_center = np.mean(g_pts[:, 1])
            w_center = np.mean(w_pts[:, 1])
            width = frame.shape[1]
            distance = (w_center - g_center) / width
            in_zone = np.min(g_pts[:, 1]) <= w_center <= np.max(g_pts[:, 1])
            return distance, in_zone, True
        return 0.0, False, False