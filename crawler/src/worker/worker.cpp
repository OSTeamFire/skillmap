#include "worker.h"
#include <nlohmann/json.hpp>
#include <gumbo.h>
#include <unistd.h>
#include <sstream>

Worker::Worker(UrlQueue& queue, int pipeFd, std::mutex& pipeMtx)
    : queue(queue), pipeFd(pipeFd), pipeMtx(pipeMtx) {}

void Worker::run() {
    while (true) {
        std::string url = queue.pop();
        if (url.empty()) break; 

        FetchResult result = fetcher.fetch(url);

        if (!result.html.empty()) {
            for (const auto& link : extractLinks(result.html, url)) {
                queue.push(link);
            }
        }

        writeToPipe(url, result.html, result.bloqueado, result.error);
    }
}

static void extractLinksFromNode(GumboNode* node, 
                                  const std::string& baseUrl,
                                  std::vector<std::string>& links) {
    if (node->type != GUMBO_NODE_ELEMENT) return;

    if (node->v.element.tag == GUMBO_TAG_A) {
        GumboAttribute* href = gumbo_get_attribute(
            &node->v.element.attributes, "href"
        );
        if (href) {
            std::string link = href->value;
            if (link.find("http") != 0) {
                link = baseUrl + link;
            }
            links.push_back(link);
        }
    }

    GumboVector* children = &node->v.element.children;
    for (unsigned int i = 0; i < children->length; i++) {
        extractLinksFromNode(
            static_cast<GumboNode*>(children->data[i]), 
            baseUrl, 
            links
        );
    }
}

std::vector<std::string> Worker::extractLinks(const std::string& html,
                                               const std::string& baseUrl) {
    std::vector<std::string> links;
    GumboOutput* output = gumbo_parse(html.c_str());
    extractLinksFromNode(output->root, baseUrl, links);
    gumbo_destroy_output(&kGumboDefaultOptions, output);
    return links;
}

void Worker::writeToPipe(const std::string& url,
                          const std::string& html,
                          bool bloqueado,
                          const std::string& error) const {
    nlohmann::json msg = {
        {"url", url},
        {"html", html},
        {"bloqueado", bloqueado},
        {"error", error}
    };

    std::string line = msg.dump() + "\n";

    std::lock_guard<std::mutex> lock(pipeMtx);
    write(pipeFd, line.c_str(), line.size());
}