#pragma once

#include <filesystem>
#include <string>
#include <vector>

struct Account { std::wstring username; std::wstring password_hash; long long expires = 0; bool developer = false; std::wstring avatar; };
struct Ticket { std::wstring id, username, title, description, category, status, created; };

class AccountService {
public:
    explicit AccountService(std::filesystem::path directory);
    bool register_user(const std::wstring& username, const std::wstring& password, std::wstring& message);
    bool login(const std::wstring& username, const std::wstring& password, std::wstring& message) const;
    void sync_remote(const std::wstring& username, bool developer, bool active);
    bool activate_promo(const std::wstring& username, const std::wstring& promo, std::wstring& message);
    bool is_developer(const std::wstring& username) const;
    bool subscription_active(const std::wstring& username) const;
    bool set_avatar(const std::wstring& username, const std::wstring& path);
    std::wstring avatar_path(const std::wstring& username) const;

private:
    std::filesystem::path path_;
    std::vector<Account> accounts_;
    void load(); void save() const;
};

class TicketService {
public:
    explicit TicketService(std::filesystem::path directory);
    bool create(const std::wstring& username, const std::wstring& title, const std::wstring& description,
                const std::wstring& category, std::wstring& message);
    std::vector<Ticket> list(const std::wstring& username, bool developer) const;

private:
    std::filesystem::path path_;
    std::vector<Ticket> tickets_;
    void load(); void save() const;
};
