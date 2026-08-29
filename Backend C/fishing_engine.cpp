#include "fishing_engine.h"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <random>
#include <string>
#include <tlhelp32.h>

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

struct ReelState {
    bool has_previous = false;
    bool indicator_seen = false;
    double previous_x = 0.0;
    int direction = 0;
    int stable_frames = 0;
    int missing_frames = 0;
};

// Returns -1 when the fish is moving left, +1 when it is moving right, and
// 0 when the fish marker cannot yet be tracked reliably.
int fish_motion_direction(const std::vector<std::uint8_t>& frame, int width, int height, int stride, ReelState& state) {
    if (frame.empty() || width < 300 || height < 200) return 0;
    const int left = int(width * 0.30), right = int(width * 0.70);
    const int top = int(height * 0.80), bottom = int(height * 0.86);
    int right_edge = -1;
    int progress_pixels = 0;
    for (int y = top; y < bottom; ++y) {
        const auto* row = frame.data() + std::ptrdiff_t(y) * stride;
        for (int x = left; x < right; ++x) {
            const auto* p = row + x * 3;
            const int b = p[0], g = p[1], r = p[2];
            // In the recording the fish icon sits at the right edge of the
            // yellow/green progress line. Tracking that colored edge is more
            // reliable than trying to recognize the tiny white fish sprite.
            if (r >= 140 && g >= 110 && b <= 120 && r + g >= 300) {
                right_edge = std::max(right_edge, x);
                ++progress_pixels;
            }
        }
    }
    if (progress_pixels < 12 || right_edge < 0) {
        if (state.indicator_seen) ++state.missing_frames;
        return 0;
    }
    state.indicator_seen = true;
    state.missing_frames = 0;
    const double x = right_edge;
    if (!state.has_previous) {
        state.has_previous = true;
        state.previous_x = x;
        return 0;
    }
    const double delta = x - state.previous_x;
    state.previous_x = x;
    if (std::abs(delta) < 1.2) return 0;
    const int direction = delta > 0.0 ? 1 : -1;
    if (direction == state.direction) ++state.stable_frames;
    else { state.direction = direction; state.stable_frames = 1; }
    return state.stable_frames >= 2 ? direction : 0;
}

TensionDecision tension_is_full_and_jerking(const std::vector<std::uint8_t>& frame, int width, int height, int stride, TensionState& state) {
    if (frame.empty() || width < 50 || height < 50) return TensionDecision::NotVisible;
    struct Bar { int x = 0; int y = 0; int width = 0; } red_bar, white_bar;
    // Majestic's tension widget is in the lower-right HUD. Restricting the
    // scan to this normalized rectangle prevents chat and notification reds
    // elsewhere on screen from being mistaken for a bite.
    const int left = int(width * 0.68), right = int(width * 0.82);
    const int top = int(height * 0.84), bottom = int(height * 0.98);
    // The bar is long and horizontal: idle is dark/white; a bite is red.
    for (int y = top; y < bottom; y += 2) {
        const auto* row = frame.data() + std::ptrdiff_t(y) * stride;
        int red_start = -1, white_start = -1;
        for (int x = left; x <= right; ++x) {
            const auto* pixel = x < right ? row + x * 3 : nullptr;
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
    const int minimum_red_width = std::max(26, int(width * 0.03));
    constexpr int kMinimumWhiteWidth = 18;
    // The inactive bar can be nearly black, with only a tiny moving white
    // marker. Treat the absence of a long red segment as the armed state.
    if (red_bar.width < minimum_red_width) {
        state.white_seen = true;
        state.red_frames = 0;
        return white_bar.width >= kMinimumWhiteWidth ? TensionDecision::WaitingForJerk : TensionDecision::NotVisible;
    }
    if (white_bar.width >= kMinimumWhiteWidth) {
        state.white_seen = true;
        state.red_frames = 0;
        state.anchor_x = white_bar.x;
        state.anchor_y = white_bar.y;
        state.anchor_width = white_bar.width;
        return TensionDecision::WaitingForJerk;
    }
    if (red_bar.width >= minimum_red_width) {
        // Require two scans so a one-frame red rendering artifact does not
        // trigger a hook. The intended event is white -> red at the same
        // screen position, not merely any red notification elsewhere in HUD.
        const bool same_indicator = state.white_seen && (state.anchor_width == 0 ||
            (std::abs(red_bar.x - state.anchor_x) <= std::max(35, state.anchor_width / 2) &&
             std::abs(red_bar.y - state.anchor_y) <= 28));
        if (same_indicator) ++state.red_frames;
        else state.red_frames = 0;
        return state.white_seen && state.red_frames >= 2 ? TensionDecision::Confirmed : TensionDecision::WaitingForJerk;
    }
    return TensionDecision::WaitingForJerk;
}

bool send_scancode(WORD scancode, DWORD flags) {
    INPUT input{};
    input.type = INPUT_KEYBOARD;
    input.ki.wScan = scancode;
    input.ki.dwFlags = flags;
    return SendInput(1, &input, sizeof(input)) == 1;
}

DWORD find_gta_process_id() {
    const HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    DWORD result = 0;
    if (Process32FirstW(snapshot, &entry)) {
        do {
            if (_wcsicmp(entry.szExeFile, L"GTA5.exe") == 0) {
                result = entry.th32ProcessID;
                break;
            }
        } while (Process32NextW(snapshot, &entry));
    }
    CloseHandle(snapshot);
    return result;
}

HWND find_largest_window_for_process(DWORD process_id) {
    struct Search { DWORD process_id; HWND result = nullptr; long long area = 0; } search{process_id};
    EnumWindows([](HWND candidate, LPARAM param) -> BOOL {
        auto* search = reinterpret_cast<Search*>(param);
        DWORD process_id = 0;
        GetWindowThreadProcessId(candidate, &process_id);
        if (process_id != search->process_id || !IsWindowVisible(candidate)) return TRUE;
        RECT rect{};
        if (!GetWindowRect(candidate, &rect)) return TRUE;
        const long long area = static_cast<long long>(rect.right - rect.left) * (rect.bottom - rect.top);
        if (area > search->area) { search->area = area; search->result = candidate; }
        return TRUE;
    }, reinterpret_cast<LPARAM>(&search));
    return search.result;
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
    const bool key_down = send_scancode(WORD(scancode), KEYEVENTF_SCANCODE);
    std::random_device device;
    std::mt19937 generator(device());
    std::uniform_int_distribution<int> delay(duration_ms, duration_ms + 20);
    std::this_thread::sleep_for(std::chrono::milliseconds(delay(generator)));
    const bool key_up = send_scancode(WORD(scancode), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP);
    return key_down && key_up ? 1 : 0;
}

FishingEngine::FishingEngine() = default;
FishingEngine::~FishingEngine() { stop(); }
const char* FishingEngine::phase_name() const {
    switch (m_phase.load()) {
    case FishingPhase::SearchingGame: return "searching for game";
    case FishingPhase::FocusingGame: return "focusing game";
    case FishingPhase::FirstE: return "sending first E";
    case FishingPhase::WaitingSecondE: return "waiting 2 seconds";
    case FishingPhase::SecondE: return "sending second E";
    case FishingPhase::Casting: return "waiting 2 seconds before cast";
    case FishingPhase::WaitingHook: return "watching tension indicator";
    case FishingPhase::Hooking: return "sending Space (hook)";
    case FishingPhase::Reeling: return "reeling A/D";
    default: return "stopped";
    }
}
void FishingEngine::tap_key(WORD scancode, int duration_ms) {
    ++m_input_attempts;
    if (fishing_tap_key(scancode, duration_ms)) ++m_input_successes;
}

bool FishingEngine::focus_game_window(HWND hwnd) const {
    if (!hwnd || !IsWindow(hwnd)) return false;
    const DWORD current_thread = GetCurrentThreadId();
    const DWORD game_thread = GetWindowThreadProcessId(hwnd, nullptr);
    const HWND foreground = GetForegroundWindow();
    const DWORD foreground_thread = foreground ? GetWindowThreadProcessId(foreground, nullptr) : 0;
    const bool attached_foreground = foreground_thread && foreground_thread != current_thread &&
        AttachThreadInput(current_thread, foreground_thread, TRUE) != FALSE;
    const bool attached_game = game_thread && game_thread != current_thread && game_thread != foreground_thread &&
        AttachThreadInput(current_thread, game_thread, TRUE) != FALSE;
    ShowWindow(hwnd, SW_RESTORE);
    BringWindowToTop(hwnd);
    SetForegroundWindow(hwnd);
    SetFocus(hwnd);
    if (attached_game) AttachThreadInput(current_thread, game_thread, FALSE);
    if (attached_foreground) AttachThreadInput(current_thread, foreground_thread, FALSE);
    return GetForegroundWindow() == hwnd;
}

GameWindowInfo FishingEngine::find_game_window() const {
    // alt:V normally owns the visible GTA window on Majestic, so do not
    // limit discovery to the old RageMP/GTA titles.
    const char* titles[] = {"Grand Theft Auto V", "Grand Theft Auto V Enhanced", "Majestic RP", "GTA5", "alt:V", "altv", "RAGE Multiplayer", "RAGEMP"};
    // The visible window title changes between alt:V states, while GTA5.exe
    // remains stable. Prefer its largest visible top-level window.
    HWND hwnd = find_largest_window_for_process(find_gta_process_id());
    if (!hwnd) {
        for (const char* title : titles) { if ((hwnd = FindWindowA(nullptr, title))) break; }
    }
    if (!hwnd) {
        struct Search { HWND result = nullptr; } search;
        EnumWindows([](HWND candidate, LPARAM param) -> BOOL {
            auto* search = reinterpret_cast<Search*>(param);
            if (!IsWindowVisible(candidate)) return TRUE;
            char title[256]{};
            GetWindowTextA(candidate, title, int(sizeof(title)));
            std::string text(title);
            std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return char(std::tolower(c)); });
            if (text.find("gta") != std::string::npos || text.find("majestic") != std::string::npos ||
                text.find("alt:v") != std::string::npos || text.find("altv") != std::string::npos ||
                text.find("rage") != std::string::npos) {
                search->result = candidate; return FALSE;
            }
            return TRUE;
        }, reinterpret_cast<LPARAM>(&search));
        hwnd = search.result;
    }
    RECT rect{};
    if (!hwnd || !GetWindowRect(hwnd, &rect)) return {};
    const int width = rect.right - rect.left, height = rect.bottom - rect.top;
    return width > 100 && height > 100 ? GameWindowInfo{true, hwnd, rect.left, rect.top, width, height} : GameWindowInfo{};
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
    m_is_active = false; m_game_found = false; m_game_focused = false; m_phase = FishingPhase::Stopped;
    m_input_attempts = 0; m_input_successes = 0;
    m_worker_thread = std::thread(&FishingEngine::main_loop, this);
}
void FishingEngine::stop() {
    m_is_running = false; m_is_active = false; m_game_found = false; m_game_focused = false; m_phase = FishingPhase::Stopped;
    if (m_worker_thread.joinable()) m_worker_thread.join();
}

void FishingEngine::main_loop() {
    while (m_is_running) {
        if (!m_is_active) { m_phase = FishingPhase::Stopped; std::this_thread::sleep_for(std::chrono::milliseconds(50)); continue; }
        m_phase = FishingPhase::SearchingGame;
        const auto window = find_game_window();
        m_game_found = window.found;
        if (!window.found) { m_game_focused = false; std::this_thread::sleep_for(std::chrono::seconds(1)); continue; }

        // The Start button makes this application's window foreground. Move
        // focus to the actual game window before sending any input.
        m_phase = FishingPhase::FocusingGame;
        m_game_focused = focus_game_window(window.handle);
        if (!m_game_focused) { std::this_thread::sleep_for(std::chrono::milliseconds(500)); continue; }
        std::this_thread::sleep_for(std::chrono::milliseconds(250));

        // Fixed fishing routine.  This intentionally does not depend on GDI
        // screen capture: the game sequence is controlled by its timings.
        m_phase = FishingPhase::FirstE;
        tap_key(SCAN_E, 110);
        // Do not cancel the sequence when Windows refuses a redundant focus
        // change after the first interaction: that was preventing the second
        // E from ever being sent in alt:V.
        m_phase = FishingPhase::WaitingSecondE;
        std::this_thread::sleep_for(std::chrono::seconds(2));
        if (!m_is_running || !m_is_active) continue;
        m_phase = FishingPhase::SecondE;
        tap_key(SCAN_E, 110);
        m_phase = FishingPhase::Casting;
        std::this_thread::sleep_for(std::chrono::seconds(2));
        if (!m_is_running || !m_is_active) continue;
        tap_key(SCAN_SPACE, 50);

        // The bite interval is random. Watch the tension widget instead of
        // using a fixed timer, and only hook after a stable red transition.
        constexpr auto hook_timeout = std::chrono::seconds(120);
        TensionState tension{};
        m_phase = FishingPhase::WaitingHook;
        const auto deadline = std::chrono::steady_clock::now() + hook_timeout;
        bool hooked = false;
        while (m_is_running && m_is_active && std::chrono::steady_clock::now() < deadline) {
            std::vector<std::uint8_t> frame;
            int width = 0, height = 0;
            if (capture_game_window(window, frame, width, height)) {
                const int stride = ((width * 3 + 3) / 4) * 4;
                if (tension_is_full_and_jerking(frame, width, height, stride, tension) == TensionDecision::Confirmed) {
                    hooked = true;
                    break;
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(30));
        }
        if (hooked) { m_phase = FishingPhase::Hooking; tap_key(SCAN_SPACE, 40); }
        m_phase = FishingPhase::Reeling;
        ReelState reel{};
        int corrections = 0;
        // The supplied recording shows this phase lasting about 49 seconds.
        // Keep following it until the progress widget disappears or 65 seconds
        // pass, rather than ending after a fixed handful of key taps.
        const auto reel_deadline = std::chrono::steady_clock::now() + std::chrono::seconds(65);
        while (hooked && m_is_running && m_is_active && corrections < 600 && reel.missing_frames < 20 &&
               std::chrono::steady_clock::now() < reel_deadline) {
            std::vector<std::uint8_t> frame;
            int width = 0, height = 0;
            int movement = 0;
            if (capture_game_window(window, frame, width, height)) {
                const int stride = ((width * 3 + 3) / 4) * 4;
                movement = fish_motion_direction(frame, width, height, stride, reel);
            }
            // A moves the line left and D moves it right, therefore pull in
            // the direction opposite to the fish's observed movement.
            if (movement > 0) { tap_key(SCAN_A, 100); ++corrections; }
            else if (movement < 0) { tap_key(SCAN_D, 100); ++corrections; }
            else std::this_thread::sleep_for(std::chrono::milliseconds(35));
        }
    }
}
