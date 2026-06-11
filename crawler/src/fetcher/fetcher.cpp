#include "fetcher.h"
#include <cpr/cpr.h>

FetchResult Fetcher::fetch(const std::string& url) const {
    FetchResult result;

    cpr::Response r = cpr::Get(
        cpr::Url{url},
        cpr::Timeout{5000}
    );

    if (r.error) {
        result.html = "";
        result.bloqueado = false;
        result.error = r.error.message;
    } else {
        result.html = r.text;
        result.bloqueado = isBloqueado(r.status_code);
        result.error = "";
    }

    return result;
}

bool Fetcher::isBloqueado(int httpCode) const {
    return httpCode == 403 || httpCode == 429;
}
