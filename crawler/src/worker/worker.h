#pragma once

#include <string>
#include <vector>
#include <mutex>
#include "../queue/queue.h"
#include "../fetcher/fetcher.h"

class Worker {
public:
    Worker(UrlQueue& queue, int pipeFd, std::mutex& pipeMtx);

    void run();

private:
    UrlQueue& queue;
    Fetcher fetcher;
    int pipeFd;
    std::mutex& pipeMtx;

    std::vector<std::string> extractLinks(const std::string& html, 
                                          const std::string& baseUrl);

    void writeToPipe(const std::string& url,
                     const std::string& html,
                     bool bloqueado,
                     const std::string& error) const;
};