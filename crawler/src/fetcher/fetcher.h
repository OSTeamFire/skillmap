#pragma once

#include <string>

struct FetchResult {
    std::string html;
    bool bloqueado;
    std::string error;
};

class Fetcher {
public:
    FetchResult fetch(const std::string& url) const;

private:
    bool isBloqueado(int httpCode) const;
};
