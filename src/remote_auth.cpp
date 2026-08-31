#include "remote_auth.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winhttp.h>

#include <algorithm>
#include <string>

namespace {
std::string utf8(const std::wstring& value) {
    if (value.empty()) return {};
    const int size = WideCharToMultiByte(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), nullptr, 0, nullptr, nullptr);
    std::string out(size, '\0');
    WideCharToMultiByte(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), out.data(), size, nullptr, nullptr);
    return out;
}
std::wstring wide(const std::string& value) {
    if (value.empty()) return {};
    const int size = MultiByteToWideChar(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), nullptr, 0);
    std::wstring out(size, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), out.data(), size);
    return out;
}
std::string escape_json(const std::string& value) {
    std::string out; out.reserve(value.size() + 8);
    for (const char c : value) { if (c == '\\' || c == '"') out.push_back('\\'); if (c == '\n') { out += "\\n"; continue; } out.push_back(c); }
    return out;
}
std::string json_string(const std::string& json, const std::string& key) {
    const auto marker = "\"" + key + "\":"; const auto start = json.find(marker); if (start == std::string::npos) return {};
    auto p = start + marker.size(); while (p < json.size() && (json[p] == ' ' || json[p] == '\t')) ++p; if (p >= json.size() || json[p] != '"') return {};
    ++p; std::string out; bool escaped = false; for (; p < json.size(); ++p) { if (escaped) { out.push_back(json[p]); escaped = false; } else if (json[p] == '\\') escaped = true; else if (json[p] == '"') break; else out.push_back(json[p]); } return out;
}
bool json_true(const std::string& json, const std::string& key) { const auto marker = "\"" + key + "\":"; const auto p = json.find(marker); return p != std::string::npos && json.find("true", p + marker.size()) < p + marker.size() + 8; }
RemoteAuthResult request(const std::wstring& path, const std::string& body) {
#ifdef MAJESTIC_SITE_URL
    std::wstring base = wide(MAJESTIC_SITE_URL);
#else
    std::wstring base = L"https://my-site-swart-rho-22.vercel.app";
#endif
    URL_COMPONENTS parts{}; parts.dwStructSize = sizeof(parts); wchar_t host[256]{}, urlPath[1024]{}; parts.lpszHostName = host; parts.dwHostNameLength = 255; parts.lpszUrlPath = urlPath; parts.dwUrlPathLength = 1023;
    if (!WinHttpCrackUrl(base.c_str(), 0, 0, &parts)) return {false, false, false, {}, L"Не удалось разобрать адрес сайта."};
    HINTERNET session = WinHttpOpen(L"MajesticAIFisher/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    HINTERNET connection = session ? WinHttpConnect(session, host, parts.nPort, 0) : nullptr;
    HINTERNET requestHandle = connection ? WinHttpOpenRequest(connection, L"POST", path.c_str(), nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, WINHTTP_FLAG_SECURE) : nullptr;
    RemoteAuthResult result; if (!requestHandle) { if (connection) WinHttpCloseHandle(connection); if (session) WinHttpCloseHandle(session); result.message = L"Сайт авторизации недоступен."; return result; }
    const std::wstring headers = L"Content-Type: application/json\r\nAccept: application/json\r\n";
    const BOOL sent = WinHttpSendRequest(requestHandle, headers.c_str(), static_cast<DWORD>(headers.size()), const_cast<char*>(body.data()), static_cast<DWORD>(body.size()), static_cast<DWORD>(body.size()), 0) && WinHttpReceiveResponse(requestHandle, nullptr);
    std::string response; if (sent) { DWORD available = 0; while (WinHttpQueryDataAvailable(requestHandle, &available) && available) { std::string chunk(available, '\0'); DWORD read = 0; if (!WinHttpReadData(requestHandle, chunk.data(), available, &read) || !read) break; response.append(chunk.data(), read); } }
    WinHttpCloseHandle(requestHandle); WinHttpCloseHandle(connection); WinHttpCloseHandle(session);
    result.ok = json_true(response, "ok"); result.active = json_true(response, "active"); result.developer = json_string(response, "role") == "admin"; result.username = wide(json_string(response, "username")); result.message = wide(json_string(response, "error")); if (result.ok && result.message.empty()) result.message = L"Авторизация успешна."; if (!result.ok && result.message.empty()) result.message = L"Неверный логин или пароль."; return result;
}
}
RemoteAuthResult remote_login(const std::wstring& identifier, const std::wstring& password) {
    return request(L"/api/client/auth", "{\"identifier\":\"" + escape_json(utf8(identifier)) + "\",\"password\":\"" + escape_json(utf8(password)) + "\"}");
}
RemoteAuthResult remote_register(const std::wstring& username, const std::wstring& email, const std::wstring& password) {
    return request(L"/api/client/register", "{\"username\":\"" + escape_json(utf8(username)) + "\",\"email\":\"" + escape_json(utf8(email)) + "\",\"password\":\"" + escape_json(utf8(password)) + "\"}");
}
