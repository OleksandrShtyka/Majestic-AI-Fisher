#pragma once

#include <windows.h>

#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>

#ifdef FISHING_NATIVE_EXPORTS
#define FISHING_API __declspec(dllexport)
#else
#define FISHING_API __declspec(dllimport)
#endif

constexpr WORD SCAN_A = 0x1E;
constexpr WORD SCAN_D = 0x20;
constexpr WORD SCAN_SPACE = 0x39;
constexpr WORD SCAN_E = 0x12;

struct GameWindowInfo {
    bool found = false;
    int x = 0;
    int y = 0;
    int w = 0;
    int h = 0;
};

class FISHING_API FishingEngine {
public:
    FishingEngine();
    ~FishingEngine();

    void start_thread();
    void stop();
    bool is_running() const { return m_is_running.load(); }
    bool is_active() const { return m_is_active.load(); }
    void set_active(bool active) { m_is_active.store(active); }

    double scale_x = 0.32;
    double scale_y = 0.78;
    double scale_w = 0.36;
    double scale_h = 0.08;

private:
    std::atomic<bool> m_is_running{false};
    std::atomic<bool> m_is_active{false};
    std::thread m_worker_thread;

    void tap_key(WORD scancode, int duration_ms = 40) const;
    GameWindowInfo find_game_window() const;
    bool capture_window_rect(const GameWindowInfo& win, std::vector<std::uint8_t>& output, int& width, int& height) const;
    void main_loop();
};

// Stable C ABI used by native_fishing.py. Image rows are BGR with `stride`
// bytes per row; the DLL never stores the input pointer.
extern "C" {
__declspec(dllexport) int fishing_process_bgr(
    const std::uint8_t* data, int width, int height, int stride,
    double* distance, int* in_zone);
__declspec(dllexport) int fishing_tap_key(unsigned short scancode, int duration_ms);
}
