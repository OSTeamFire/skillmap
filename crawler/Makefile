CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -pthread
LIBS = -lcpr -lgumbo -lcurl -lssl -lcrypto

SRC = src/main.cpp \
      src/worker/worker.cpp \
      src/queue/queue.cpp \
      src/fetcher/fetcher.cpp

TARGET = build/crawler

$(TARGET): $(SRC)
	mkdir -p build
	$(CXX) $(CXXFLAGS) $(SRC) -o $(TARGET) $(LIBS)

clean:
	rm -rf build