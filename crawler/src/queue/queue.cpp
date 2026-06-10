#include "queue.h"

void UrlQueue::push(const std::string& url) {
    std::lock_guard<std::mutex> lock(mtx);
    if (visited.find(url) == visited.end()) {
        pending.push(url);
        visited.insert(url);
        cv.notify_one(); // Despierta un worker
    }
}

std::string UrlQueue::pop() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, [this] {
        return !pending.empty() || done;
    });
    if (pending.empty()) return ""; // Sistema apagándose
    std::string url = pending.front();
    pending.pop();
    return url;
}

bool UrlQueue::isEmpty() {
    std::lock_guard<std::mutex> lock(mtx);
    return pending.empty();
}

void UrlQueue::shutdown() {
    std::lock_guard<std::mutex> lock(mtx);
    done = true;
    cv.notify_all(); // Despierta todos los workers para que terminen
}
