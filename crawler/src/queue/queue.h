#pragma once

#include <queue>
#include <unordered_set>
#include <string>
#include <mutex>
#include <condition_variable>

class UrlQueue {
public:
    void push(const std::string& url);
    
    // Bloquea el worker hasta que haya una URL disponible
    std::string pop();
    
    bool isEmpty();
    
    // Despierta todos los workers para que puedan terminar
    void shutdown();

private:
    std::queue<std::string> pending;
    std::unordered_set<std::string> visited;
    std::mutex mtx;
    std::condition_variable cv;
    bool done = false;
};
