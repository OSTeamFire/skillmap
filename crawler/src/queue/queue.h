#pragma once

#include <queue>
#include <unordered_set>
#include <string>
#include <mutex>

class UrlQueue {
public:
    // Agrega una URL si no ha sido visitada antes
    void push(const std::string& url);

    // Saca y retorna la siguiente URL. Retorna "" si está vacía
    std::string pop();

    // Retorna true si no hay URLs pendientes
    bool isEmpty();

private:
    std::queue<std::string> pending;
    std::unordered_set<std::string> visited;
    std::mutex mtx;
};
