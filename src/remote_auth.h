#pragma once

#include <string>

struct RemoteAuthResult {
    bool ok = false;
    bool active = false;
    bool developer = false;
    std::wstring username;
    std::wstring message;
};

RemoteAuthResult remote_login(const std::wstring& identifier, const std::wstring& password);
RemoteAuthResult remote_register(const std::wstring& username, const std::wstring& email, const std::wstring& password);
