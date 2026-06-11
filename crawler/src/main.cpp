#include <iostream>
#include <thread>
#include <vector>
#include <mutex>
#include <chrono>
#include <unistd.h>
#include <string>
#include "worker/worker.h"
#include "queue/queue.h"

int main(int argc, char* argv[]) {
    // --- Argumentos CLI ---
    std::string seedUrl;
    int tiempo     = 60;
    int numWorkers = 4;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--url" && i + 1 < argc)          seedUrl    = argv[++i];
        else if (arg == "--tiempo" && i + 1 < argc)  tiempo     = std::stoi(argv[++i]);
        else if (arg == "--workers" && i + 1 < argc) numWorkers = std::stoi(argv[++i]);
    }

    if (seedUrl.empty()) {
        std::cerr << "Error: se requiere --url\n";
        return 1;
    }

    // --- Inicializar cola ---
    UrlQueue queue;
    queue.push(seedUrl);

    // --- Mutex compartido para stdout ---
    std::mutex pipeMtx;

    // --- Lanzar workers ---
    std::vector<std::thread> workers;
    for (int i = 0; i < numWorkers; i++) {
        workers.emplace_back([&queue, &pipeMtx]() {
            Worker worker(queue, STDOUT_FILENO, pipeMtx);
            worker.run();
        });
    }

    // --- Esperar X segundos ---
    std::this_thread::sleep_for(std::chrono::seconds(tiempo));

    // --- Apagar cola y esperar workers ---
    queue.shutdown();
    for (auto& t : workers) t.join();

    return 0;
}