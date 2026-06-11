CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -pthread
LIBS = -lcpr -lgumbo -lcurl

SRC = src/main.cpp \
      src/worker/worker.cpp \
      src/queue/queue.cpp \
      src/fetcher/fetcher.cpp

TARGET = skillmap

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(TARGET) $(LIBS)

clean:
	rm -f $(TARGET)