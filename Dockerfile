FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    g++ cmake git \
    libcurl4-openssl-dev \
    libssl-dev \
    libgumbo-dev \
    nlohmann-json3-dev \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Compilar cpr desde fuente
RUN git clone https://github.com/libcpr/cpr.git /tmp/cpr && \
    cmake -B /tmp/cpr/build -S /tmp/cpr \
        -DCPR_USE_SYSTEM_CURL=ON \
        -DCPR_FORCE_OPENSSL_BACKEND=ON && \
    cmake --build /tmp/cpr/build --parallel && \
    cmake --install /tmp/cpr/build && \
    rm -rf /tmp/cpr

WORKDIR /app

# Dependencias Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar proyecto y compilar crawler
COPY . .
RUN make -C crawler

ENTRYPOINT ["python3", "main.py"]