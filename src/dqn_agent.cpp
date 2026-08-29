#include "dqn_agent.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <numeric>

namespace { constexpr char kMagic[] = "MAJESTIC_DQN_V1"; constexpr float kRate = 0.0015f; }

DqnAgent::DqnAgent() : rng_(std::random_device{}()) {
    std::normal_distribution<float> init(0.0f, 0.08f);
    for (auto& row : w1_) for (auto& item : row) item = init(rng_);
    for (auto& row : w2_) for (auto& item : row) item = init(rng_);
}

std::array<float, DqnAgent::action_size> DqnAgent::predict(const std::array<float, state_size>& state, Hidden* hidden) const {
    Hidden h{};
    for (int i = 0; i < hidden_size; ++i) {
        h[i] = b1_[i];
        for (int j = 0; j < state_size; ++j) h[i] += w1_[i][j] * state[j];
        h[i] = std::max(0.0f, h[i]);
    }
    if (hidden) *hidden = h;
    std::array<float, action_size> q{};
    for (int action = 0; action < action_size; ++action) {
        q[action] = b2_[action];
        for (int i = 0; i < hidden_size; ++i) q[action] += w2_[action][i] * h[i];
    }
    return q;
}

int DqnAgent::choose_action(const std::array<float, state_size>& state, bool explore) {
    std::uniform_real_distribution<float> unit(0.0f, 1.0f);
    if (explore && unit(rng_) < epsilon_) return std::uniform_int_distribution<int>(0, action_size - 1)(rng_);
    const auto q = predict(state);
    return q[1] > q[0] ? 1 : 0;
}

void DqnAgent::observe(const std::array<float, state_size>& s, int action, float reward,
                       const std::array<float, state_size>& next, bool done) {
    if (action < 0 || action >= action_size) return;
    if (memory_.size() == 10000) memory_.pop_front();
    memory_.push_back({s, next, action, reward, done});
}

float DqnAgent::train_step() {
    if (memory_.size() < 32) return 0.0f;
    std::uniform_int_distribution<std::size_t> pick(0, memory_.size() - 1);
    float loss = 0.0f;
    for (int sample = 0; sample < 32; ++sample) {
        const auto& t = memory_[pick(rng_)];
        Hidden h{};
        const auto q = predict(t.s, &h);
        const auto next_q = predict(t.next);
        const float target = t.reward + (t.done ? 0.0f : 0.98f * std::max(next_q[0], next_q[1]));
        const float error = std::clamp(q[t.action] - target, -10.0f, 10.0f);
        loss += error * error;
        std::array<float, hidden_size> hidden_gradient{};
        for (int i = 0; i < hidden_size; ++i) {
            hidden_gradient[i] = error * w2_[t.action][i] * (h[i] > 0.0f ? 1.0f : 0.0f);
            w2_[t.action][i] -= kRate * error * h[i];
        }
        b2_[t.action] -= kRate * error;
        for (int i = 0; i < hidden_size; ++i) {
            for (int j = 0; j < state_size; ++j) w1_[i][j] -= kRate * hidden_gradient[i] * t.s[j];
            b1_[i] -= kRate * hidden_gradient[i];
        }
    }
    epsilon_ = std::max(0.03f, epsilon_ * 0.998f);
    return loss / 32.0f;
}

bool DqnAgent::save(const std::filesystem::path& path) const {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return false;
    out.write(kMagic, sizeof(kMagic));
    out.write(reinterpret_cast<const char*>(&epsilon_), sizeof(epsilon_));
    out.write(reinterpret_cast<const char*>(w1_.data()), sizeof(w1_)); out.write(reinterpret_cast<const char*>(b1_.data()), sizeof(b1_));
    out.write(reinterpret_cast<const char*>(w2_.data()), sizeof(w2_)); out.write(reinterpret_cast<const char*>(b2_.data()), sizeof(b2_));
    return bool(out);
}

bool DqnAgent::load(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    char magic[sizeof(kMagic)]{};
    if (!in || !in.read(magic, sizeof(magic)) || std::string(magic) != kMagic) return false;
    in.read(reinterpret_cast<char*>(&epsilon_), sizeof(epsilon_));
    in.read(reinterpret_cast<char*>(w1_.data()), sizeof(w1_)); in.read(reinterpret_cast<char*>(b1_.data()), sizeof(b1_));
    in.read(reinterpret_cast<char*>(w2_.data()), sizeof(w2_)); in.read(reinterpret_cast<char*>(b2_.data()), sizeof(b2_));
    return bool(in);
}
