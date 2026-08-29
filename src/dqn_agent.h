#pragma once

#include <array>
#include <deque>
#include <filesystem>
#include <random>

class DqnAgent {
public:
    static constexpr int state_size = 4;
    static constexpr int hidden_size = 32;
    static constexpr int action_size = 2;

    DqnAgent();
    int choose_action(const std::array<float, state_size>& state, bool explore = true);
    void observe(const std::array<float, state_size>& state, int action, float reward,
                 const std::array<float, state_size>& next_state, bool done);
    float train_step();
    bool load(const std::filesystem::path& path);
    bool save(const std::filesystem::path& path) const;
    std::size_t memory_size() const { return memory_.size(); }
    float epsilon() const { return epsilon_; }

private:
    struct Transition { std::array<float, state_size> s, next; int action; float reward; bool done; };
    using Hidden = std::array<float, hidden_size>;
    std::array<std::array<float, state_size>, hidden_size> w1_{};
    std::array<float, hidden_size> b1_{};
    std::array<std::array<float, hidden_size>, action_size> w2_{};
    std::array<float, action_size> b2_{};
    std::deque<Transition> memory_;
    std::mt19937 rng_;
    float epsilon_ = 0.20f;
    std::array<float, action_size> predict(const std::array<float, state_size>& state, Hidden* hidden = nullptr) const;
};
