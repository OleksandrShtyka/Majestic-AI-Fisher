#include "app_services.h"

#include <windows.h>
#include <bcrypt.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <random>
#include <sstream>

namespace {
long long now_seconds() { return std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count(); }
std::wstring trim(std::wstring value) {
    const auto first = value.find_first_not_of(L" \t\r\n"), last = value.find_last_not_of(L" \t\r\n");
    return first == std::wstring::npos ? L"" : value.substr(first, last - first + 1);
}
std::wstring hex_bytes(const unsigned char* bytes, std::size_t count) {
    static constexpr wchar_t digits[] = L"0123456789abcdef";
    std::wstring result(count * 2, L'0');
    for (std::size_t i = 0; i < count; ++i) { result[i * 2] = digits[bytes[i] >> 4]; result[i * 2 + 1] = digits[bytes[i] & 15]; }
    return result;
}
std::wstring password_hash(const std::wstring& username, const std::wstring& password) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    std::array<unsigned char, 32> output{};
    const auto status = BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, BCRYPT_ALG_HANDLE_HMAC_FLAG);
    if (status < 0) return L"";
    const auto derive = BCryptDeriveKeyPBKDF2(algorithm,
        reinterpret_cast<PUCHAR>(const_cast<wchar_t*>(password.data())), static_cast<ULONG>(password.size() * sizeof(wchar_t)),
        reinterpret_cast<PUCHAR>(const_cast<wchar_t*>(username.data())), static_cast<ULONG>(username.size() * sizeof(wchar_t)),
        100000, output.data(), static_cast<ULONG>(output.size()), 0);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    return derive >= 0 ? hex_bytes(output.data(), output.size()) : L"";
}
std::vector<std::wstring> split(const std::wstring& value, wchar_t delimiter) {
    std::wstringstream stream(value); std::wstring item; std::vector<std::wstring> result;
    while (std::getline(stream, item, delimiter)) result.push_back(item); return result;
}
bool valid_field(const std::wstring& value) { return !value.empty() && value.find_first_of(L"\\/:*?\"<>|\t\r\n") == std::wstring::npos; }
}

AccountService::AccountService(std::filesystem::path directory) : path_(std::move(directory) / L"accounts.dat") { load(); }
void AccountService::load() {
    std::wifstream file(path_); std::wstring line;
    while (std::getline(file, line)) {
        auto fields = split(line, L'\t');
        if (fields.size() >= 4) {
            try { accounts_.push_back({fields[0], fields[1], std::stoll(fields[2]), fields[3] == L"1", fields.size() > 4 ? fields[4] : L""}); } catch (...) {}
        }
    }
    for (const wchar_t* name : {L"admin", L"Developer", L"pogo"}) {
        if (std::none_of(accounts_.begin(), accounts_.end(), [&](const Account& account) { return account.username == name; }))
            accounts_.push_back({name, password_hash(name, L"12345"), now_seconds() + 36500LL * 86400, true});
    }
    save();
}
void AccountService::save() const { std::wofstream file(path_, std::ios::trunc); for (const auto& a : accounts_) file << a.username << L'\t' << a.password_hash << L'\t' << a.expires << L'\t' << (a.developer ? 1 : 0) << L'\t' << a.avatar << L'\n'; }
bool AccountService::register_user(const std::wstring& raw_username, const std::wstring& password, std::wstring& message) {
    const auto username = trim(raw_username);
    if (!valid_field(username) || password.size() < 4) { message = L"Укажите логин и пароль не короче 4 символов."; return false; }
    if (std::any_of(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; })) { message = L"Пользователь уже существует."; return false; }
    accounts_.push_back({username, password_hash(username, password), now_seconds() + 3LL * 86400, false}); save(); message = L"Регистрация успешна: триал активен 3 дня."; return true;
}
bool AccountService::login(const std::wstring& raw_username, const std::wstring& password, std::wstring& message) const {
    const auto username = trim(raw_username); const auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; });
    if (it == accounts_.end() || it->password_hash != password_hash(username, password)) { message = L"Неверный логин или пароль."; return false; }
    if (!it->developer && it->expires < now_seconds()) { message = L"Срок подписки истёк."; return false; }
    message = L"Авторизация успешна."; return true;
}
void AccountService::sync_remote(const std::wstring& username, bool developer, bool active) {
    auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; });
    const long long expires = active ? now_seconds() + 86400 : 0;
    if (it == accounts_.end()) accounts_.push_back({username, L"", expires, developer});
    else { it->expires = expires; it->developer = developer; }
    save();
}
bool AccountService::activate_promo(const std::wstring& username, const std::wstring& promo, std::wstring& message) {
    auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; });
    if (it == accounts_.end()) { message = L"Пользователь не найден."; return false; }
    if (it->developer) { message = L"У разработчика вечная подписка."; return true; }
    const int days = promo == L"MAJESTIC30" ? 30 : promo == L"PROMO7" ? 7 : promo == L"VIP365" ? 365 : 0;
    if (!days) { message = L"Неверный промокод."; return false; }
    it->expires = std::max(it->expires, now_seconds()) + static_cast<long long>(days) * 86400; save(); message = L"Подписка продлена."; return true;
}
bool AccountService::is_developer(const std::wstring& username) const { auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; }); return it != accounts_.end() && it->developer; }
bool AccountService::subscription_active(const std::wstring& username) const { auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; }); return it != accounts_.end() && (it->developer || it->expires >= now_seconds()); }
bool AccountService::set_avatar(const std::wstring& username, const std::wstring& path) { auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; }); if (it == accounts_.end()) return false; it->avatar = path; save(); return true; }
std::wstring AccountService::avatar_path(const std::wstring& username) const { auto it = std::find_if(accounts_.begin(), accounts_.end(), [&](const Account& a) { return a.username == username; }); return it == accounts_.end() ? L"" : it->avatar; }

TicketService::TicketService(std::filesystem::path directory) : path_(std::move(directory) / L"tickets.dat") { load(); }
void TicketService::load() { std::wifstream file(path_); std::wstring line; while (std::getline(file, line)) { auto f = split(line, L'|'); if (f.size() == 7) tickets_.push_back({f[0], f[1], f[2], f[3], f[4], f[5], f[6]}); } }
void TicketService::save() const { std::wofstream file(path_, std::ios::trunc); for (const auto& t : tickets_) file << t.id << L'|' << t.username << L'|' << t.title << L'|' << t.description << L'|' << t.category << L'|' << t.status << L'|' << t.created << L'\n'; }
bool TicketService::create(const std::wstring& username, const std::wstring& title, const std::wstring& description, const std::wstring& category, std::wstring& message) {
    if (!valid_field(title) || !valid_field(description) || !valid_field(category)) { message = L"Заполните все поля тикета."; return false; }
    std::mt19937 rng(std::random_device{}()); wchar_t id[9]; swprintf_s(id, L"%08X", rng());
    tickets_.push_back({id, username, title, description, category, L"Открыт", std::to_wstring(now_seconds())}); save(); message = L"Тикет создан: #" + std::wstring(id); return true;
}
std::vector<Ticket> TicketService::list(const std::wstring& username, bool developer) const { std::vector<Ticket> result; for (const auto& ticket : tickets_) if (developer || ticket.username == username) result.push_back(ticket); return result; }
