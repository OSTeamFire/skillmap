#pragma once

#include <string>

struct FetchResult {
    std::string html;
    bool bloqueado;
    std::string error; // "" si no hubo error
};

class Fetcher {
public:
    // Descarga la página y retorna el resultado
    FetchResult fetch(const std::string& url);

private:
    // Interpreta el código HTTP y determina si fue bloqueado
    bool isBloqueado(int httpCode);
};
