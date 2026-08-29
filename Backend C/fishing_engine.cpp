#include "fishing_engine.h"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <random>
#include <string>

namespace {

bool is_green(std::uint8_t b, std::uint8_t g, std::uint8_t r) {
    const int maximum = std::max({int(b), int(g), int(r)});
    const int minimum = std::min({int(b), int(g), int(r)});
    if (maximum < 40 || maximum == minimum) return false;
    const int saturation = (maximum - minimum) * 255 / maximum;
    if (saturation < 40) return false;
    double hue = maximum == r ? 60.0 * (int(g) - int(b)) / (maximum - minimum)
               : maximum == g ? 120.0 + 60.0 * (int(b) - int(r)) / (maximum - minimum)
                              : 240.0 + 60.0 * (int(r) - int(g)) / (maximum - minimum);
    if (hue < 0.0) hue += 360.0;
    return hue / 2.0 >= 35.0 && hue / 2.0 <= 90.0;
}

bool is_white(std::uint8_t b, std::uint8_t g, std::uint8_t r) {
    const int maximum = std::max({int(b), int(g), int(r)});
    const int minimum = std::min({int(b), int(g), int(r)});
    return maximum >= 180 && (maximum - minimum) * 255 / maximum <= 60;
}

bool parse_bgr(const std::uint8_t* data, int width, int height, int stride, double& distance, bool& in_zone) {
    if (!data || width <= 0 || height <= 0 || stride < width * 3) return false;
    std::int64_t green_sum = 0, white_sum = 0;
    int green_count = 0, green_min = width, green_max = -1, green_min_y = height, green_max_y = -1;
    for (int y = 0; y < height; ++y) {
        const auto* row = data + std::ptrdiff_t(y) * stride;
        for (int x = 0; x < width; ++x) {
            const auto* pixel = row + x * 3;
            if (is_green(pixel[0], pixel[1], pixel[2])) {
                green_sum += x; ++green_count;
                green_min = std::min(green_min, x); green_max = std::max(green_max, x);
                green_min_y = std::min(green_min_y, y); green_max_y = std::max(green_max_y, y);
            }
        }
    }
    if (green_count <= 5) return false;
    // Only accept the white marker in the same horizontal strip as the green
    // casting zone. This avoids white text/cursors elsewhere in the HUD.
    int white_count = 0;
    const int marker_top = std::max(0, green_min_y - 18), marker_bottom = std::min(height, green_max_y + 19);
    for (int y = marker_top; y < marker_bottom; ++y) {
        const auto* row = data + std::ptrdiff_t(y) * stride;
        for (int x = std::max(0, green_min - 25); x < std::min(width, green_max + 26); ++x) {
            const auto* pixel = row + x * 3;
            if (is_white(pixel[0], pixel[1], pixel[2])) { white_sum += x; ++white_count; }
        }
    }
    if (white_count == 0) return false;
    const double green_center = double(green_sum) / green_count;
    const double white_center = double(white_sum) / white_count;
    distance = (white_center - green_center) / width;
    in_zone = green_min - 5 <= white_center && white_center <= green_max + 5;
    return true;
}

bool is_tension_red(const std::uint8_t* pixel) {
    // Saturated red state of the horizontal "Tension" bar.
    return pixel[2] >= 135 && pixel[2] >= pixel[1] * 2 && pixel[2] >= pixel[0] * 2;
}

struct TensionState {
    bool white_seen = false;
    int red_frames = 0;
    int anchor_x = 0;
    int anchor_y = 0;
    int anchor_width = 0;
};

enum class TensionDecision { NotVisible, WaitingForJerk, Confirmed };

TensionDecision tension_is_full_and_jerking(const std::vector<std::uint8_t>& frame, int width, int height, int stride, TensionState& state) {
    if (frame.empty() || width < 50 || height < 50) return TensionDecision::NotVisible;
    struct Bar { int x = 0; int y = 0; int width = 0; } red_bar, white_bar;
    // The indicator is a long horizontal line: white when idle and red at a
    // bite. Ignore short text strokes and other HUD elements.
    for (int y = 0; y < height; y += 2) {
        const auto* row = frame.data() + std::ptrdiff_t(y) * stride;
        int red_start = -1, white_start = -1;
        for (int x = 0; x <= width; ++x) {
            const auto* pixel = x < width ? row + x * 3 : nullptr;
            const bool red = pixel && is_tension_red(pixel);
            const int high = pixel ? std::max({int(pixel[0]), int(pixel[1]), int(pixel[2])}) : 0;
            const int low = pixel ? std::min({int(pixel[0]), int(pixel[1]), int(pixel[2])}) : 0;
            const bool white = pixel && high >= 185 && high - low <= 45;
            if (red && red_start < 0) red_start = x;
            if (white && white_start < 0) white_start = x;
            if ((!red || x == width) && red_start >= 0) {
                const int run = x - red_start;
                if (run > red_bar.width) red_bar = {red_start, y, run};
                red_start = -1;
            }
            if ((!white || x == width) && white_start >= 0) {
                const int run = x - white_start;
                if (run > white_bar.width) white_bar = {white_start, y, run};
                white_start = -1;
            }
        }
    }
    constexpr int kMinimumBarWidth = 42;
    if (red_bar.width < kMinimumBarWidth && white_bar.width < kMinimumBarWidth) return TensionDecision::NotVisible;
    if (white_bar.width >= kMinimumBarWidth) {
        state.white_seen = true;
        state.red_frames = 0;
        state.anchor_x = white_bar.x;
        state.anchor_y = white_bar.y;
        state.anchor_width = white_bar.width;
        return TensionDecision::WaitingForJerk;
    }
    if (red_bar.width >= kMinimumBarWidth) {
        // Require two scans so a one-frame red rendering artifact does not
        // trigger a hook. The intended event is white -> red at the same
        // screen position, not merely any red notification elsewhere in HUD.
        const bool same_indicator = state.white_seen &&
            std::abs(red_bar.x - state.anchor_x) <= std::max(35, state.anchor_width / 2) &&
            std::abs(red_bar.y - state.anchor_y) <= 28;
        if (same_indicator) ++state.red_frames;
        else state.red_frames = 0;
        return state.white_seen && state.red_frames >= 2 ? TensionDecision::Confirmed : TensionDecision::WaitingForJerk;
    }
    return TensionDecision::WaitingForJerk;
}

void send_scancode(WORD scancode, DWORD flags) {
    INPUT input{};
    input.type = INPUT_KEYBOARD;
    input.ki.wScan = scancode;
    input.ki.dwFlags = flags;
    SendInput(1, &input, sizeof(input));
}

}  // namespace

extern "C" int fishing_process_bgr(const std::uint8_t* data, int width, int height, int stride,
                                    double* distance, int* in_zone) {
    if (!distance || !in_zone) return 0;
    bool inside = false;
    double result_distance = 0.0;
    const bool found = parse_bgr(data, width, height, stride, result_distance, inside);
    *distance = result_distance;
    *in_zone = inside ? 1 : 0;
    return found ? 1 : 0;
}

extern "C" int fishing_tap_key(unsigned short scancode, int duration_ms) {
    if (duration_ms < 0 || duration_ms > 5000) return 0;
    send_scancode(WORD(scancode), KEYEVENTF_SCANCODE);
    std::random_device device;
    std::mt19937 generator(device());
    std::uniform_int_distribution<int> delay(duration_ms, duration_ms + 20);
    std::this_thread::sleep_for(std::chrono::milliseconds(delay(generator)));
    send_scancode(WORD(scancode), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP);
    return 1;
}

FishingEngine::FishingEngine() = default;
FishingEngine::~FishingEngine() { stop(); }
void FishingEngine::tap_key(WORD scancode, int duration_ms) const { fishing_tap_key(scancode, duration_ms); }

GameWindowInfo FishingEngine::find_game_window() const {
    const char* titles[] = {"Grand Theft Auto V", "Majestic RP", "GTA5", "RAGE Multiplayer", "RAGEMP"};
    HWND hwnd = nullptr;
    for (const char* title : titles) { if ((hwnd = FindWindowA(nullptr, title))) break; }
    if (!hwnd) {
        struct Search { HWND result = nullptr; } search;
        EnumWindows([](HWND candidate, LPARAM param) -> BOOL {
            auto* search = reinterpret_cast<Search*>(param);
            if (!IsWindowVisible(candidate)) return TRUE;
            char title[256]{};
            GetWindowTextA(candidate, title, int(sizeof(title)));
            std::string text(title);
            std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return char(std::tolower(c)); });
            if (text.find("gta") != std::string::npos || text.find("majestic") != std::string::npos || text.find("rage") != std::string::npos) {
                search->result = candidate; return FALSE;
            }
            return TRUE;
        }, reinterpret_cast<LPARAM>(&search));
        hwnd = search.result;
    }
    RECT rect{};
    if (!hwnd || !GetWindowRect(hwnd, &rect)) return {};
    const int width = rect.right - rect.left, height = rect.bottom - rect.top;
    return width > 100 && height > 100 ? GameWindowInfo{true, rect.left, rect.top, width, height} : GameWindowInfo{};
}

bool FishingEngine::capture_window_rect(const GameWindowInfo& win, std::vector<std::uint8_t>& output, int& width, int& height) const {
    width = std::max(20, int(win.w * scale_w)); height = std::max(10, int(win.h * scale_h));
    const int x = win.x + int(win.w * scale_x), y = win.y + int(win.h * scale_y);
    HWND desktop = GetDesktopWindow(); HDC screen = GetDC(desktop);
    HDC memory = screen ? CreateCompatibleDC(screen) : nullptr;
    HBITMAP bitmap = memory ? CreateCompatibleBitmap(screen, width, height) : nullptr;
    if (!screen || !memory || !bitmap) {
        if (bitmap) DeleteObject(bitmap); if (memory) DeleteDC(memory); if (screen) ReleaseDC(desktop, screen);
        return false;
    }
    HGDIOBJ previous = SelectObject(memory, bitmap);
    const bool copied = BitBlt(memory, 0, 0, width, height, screen, x, y, SRCCOPY | CAPTUREBLT) != 0;
    BITMAPINFO info{};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER); info.bmiHeader.biWidth = width; info.bmiHeader.biHeight = -height;
    info.bmiHeader.biPlanes = 1; info.bmiHeader.biBitCount = 24; info.bmiHeader.biCompression = BI_RGB;
    const int stride = ((width * 3 + 3) / 4) * 4;
    output.resize(size_t(stride) * height);
    const bool read = GetDIBits(memory, bitmap, 0, height, output.data(), &info, DIB_RGB_COLORS) != 0;
    SelectObject(memory, previous); DeleteObject(bitmap); DeleteDC(memory); ReleaseDC(desktop, screen);
    return copied && read;
}

bool FishingEngine::capture_game_window(const GameWindowInfo& win, std::vector<std::uint8_t>& output, int& width, int& height) const {
    width = win.w; height = win.h;
    HWND desktop = GetDesktopWindow(); HDC screen = GetDC(desktop);
    HDC memory = screen ? CreateCompatibleDC(screen) : nullptr;
    HBITMAP bitmap = memory ? CreateCompatibleBitmap(screen, width, height) : nullptr;
    if (!screen || !memory || !bitmap) {
        if (bitmap) DeleteObject(bitmap); if (memory) DeleteDC(memory); if (screen) ReleaseDC(desktop, screen);
        return false;
    }
    HGDIOBJ previous = SelectObject(memory, bitmap);
    const bool copied = BitBlt(memory, 0, 0, width, height, screen, win.x, win.y, SRCCOPY | CAPTUREBLT) != 0;
    BITMAPINFO info{}; info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER); info.bmiHeader.biWidth = width; info.bmiHeader.biHeight = -height;
    info.bmiHeader.biPlanes = 1; info.bmiHeader.biBitCount = 24; info.bmiHeader.biCompression = BI_RGB;
    const int stride = ((width * 3 + 3) / 4) * 4; output.resize(size_t(stride) * height);
    const bool read = GetDIBits(memory, bitmap, 0, height, output.data(), &info, DIB_RGB_COLORS) != 0;
    SelectObject(memory, previous); DeleteObject(bitmap); DeleteDC(memory); ReleaseDC(desktop, screen);
    return copied && read;
}

void FishingEngine::start_thread() {
    if (m_is_running.exchange(true)) return;
    m_is_active = false; m_worker_thread = std::thread(&FishingEngine::main_loop, this);
}
void FishingEngine::stop() {
    m_is_running = false; m_is_active = false;
    if (m_worker_thread.joinable()) m_worker_thread.join();
}

void FishingEngine::main_loop() {
    bool last_hotkey = false;
    while (m_is_running) {
        const bool hotkey = (GetAsyncKeyState(VK_F5) & 0x8000) != 0;
        if (hotkey && !last_hotkey) m_is_active = !m_is_active.load();
        last_hotkey = hotkey;
        if (!m_is_active) { std::this_thread::sleep_for(std::chrono::milliseconds(50)); continue; }
        const auto window = find_game_window();
        if (!window.found) { std::this_thread::sleep_for(std::chrono::seconds(1)); continue; }
        // Phase 1: cast only when the white marker reaches the green launch
        // zone on the long horizontal casting bar.
        const auto cast_start = std::chrono::steady_clock::now();
        bool casted = false;
        while (m_is_running && m_is_active && std::chrono::steady_clock::now() - cast_start < std::chrono::seconds(12)) {
            std::vector<std::uint8_t> frame; int width = 0, height = 0;
            // Prefer the user-configured capture zone. If it does not find
            // the scale quickly, scan the whole window before using fallback.
            const auto cast_elapsed = std::chrono::steady_clock::now() - cast_start;
            const bool use_configured_zone = cast_elapsed < std::chrono::milliseconds(1200);
            const bool captured = use_configured_zone
                ? capture_window_rect(window, frame, width, height)
                : capture_game_window(window, frame, width, height);
            if (captured) {
                double distance = 0.0; bool in_green_zone = false;
                const int stride = ((width * 3 + 3) / 4) * 4;
                if (parse_bgr(frame.data(), width, height, stride, distance, in_green_zone) && in_green_zone) {
                    // The launch bar is confirmed with Space when its white
                    // marker reaches the green segment.
                    tap_key(SCAN_SPACE, 50);
                    casted = true;
                    break;
                }
            }
            // Some game modes hide the launch scale from GDI capture. Do not
            // leave the bot idle forever: start the cast after a short wait.
            if (cast_elapsed >= std::chrono::milliseconds(3200)) {
                tap_key(SCAN_SPACE, 50);
                casted = true;
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        if (!casted) continue;

        std::this_thread::sleep_for(std::chrono::milliseconds(1500));
        // Phase 2: wait for the separate tension indicator to change from
        // white (idle) to red (bite), then hook with Space.
        const auto wait_start = std::chrono::steady_clock::now(); bool hooked = false;
        TensionState tension_state;
        auto last_tension_scan = wait_start;
        while (m_is_running && m_is_active && std::chrono::steady_clock::now() - wait_start < std::chrono::seconds(12)) {
            const auto now = std::chrono::steady_clock::now();
            if (now - last_tension_scan >= std::chrono::milliseconds(45)) {
                std::vector<std::uint8_t> hud; int hud_width = 0, hud_height = 0;
                last_tension_scan = now;
                const int hud_stride = ((window.w * 3 + 3) / 4) * 4;
                if (capture_game_window(window, hud, hud_width, hud_height)) {
                    const auto tension = tension_is_full_and_jerking(hud, hud_width, hud_height, hud_stride, tension_state);
                    if (tension == TensionDecision::Confirmed) {
                        tap_key(SCAN_SPACE, 40); hooked = true; break;
                    }
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        const auto reel_start = std::chrono::steady_clock::now();
        while (hooked && m_is_running && m_is_active && std::chrono::steady_clock::now() - reel_start < std::chrono::seconds(6)) {
            tap_key(SCAN_A, 60); std::this_thread::sleep_for(std::chrono::milliseconds(80));
            tap_key(SCAN_D, 60); std::this_thread::sleep_for(std::chrono::milliseconds(80));
        }
    }
}
