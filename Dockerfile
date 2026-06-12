# ---- Etapa 1: construir CPR una sola vez ----
FROM ubuntu:22.04 AS cpr-builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    g++ cmake git \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/libcpr/cpr.git /tmp/cpr && \
    cmake -B /tmp/cpr/build -S /tmp/cpr \
        -DCPR_USE_SYSTEM_CURL=ON \
        -DCPR_FORCE_OPENSSL_BACKEND=ON && \
    cmake --build /tmp/cpr/build --parallel && \
    cmake --install /tmp/cpr/build && \
    rm -rf /tmp/cpr

# ---- Etapa 2: imagen final ----
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    g++ \
    libcurl4-openssl-dev \
    libssl-dev \
    libgumbo-dev \
    nlohmann-json3-dev \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copiar CPR ya compilado desde etapa 1
COPY --from=cpr-builder /usr/local /usr/local

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN make -C crawler

ENTRYPOINT ["python3", "main.py"]