# SkillMap

Análisis de demanda de habilidades tecnológicas en el mercado laboral hispanohablante mediante web crawling concurrente híbrido C++/Python.

**Proyecto final — Sistemas Operativos y Laboratorio, Universidad de Antioquia, 2026.**

---

## Descripción

SkillMap rastrea ofertas de trabajo tech desde una URL semilla, extrae las habilidades técnicas mencionadas en cada página y genera tres artefactos: un ranking de frecuencias, un grafo de co-ocurrencias entre habilidades, y un índice de apertura de plataformas (qué sitios permiten rastreo automatizado y cuáles no).

El proyecto demuestra conceptos de Sistemas Operativos en contexto real:

- **IPC mediante pipe**: el crawler C++ escribe JSON en `stdout`; Python lo lee línea a línea en tiempo real.
- **Concurrencia con pthreads**: múltiples workers C++ comparten una cola sincronizada con `mutex` y `condition_variable`.
- **Manejo de señales**: `SIGINT` dispara guardado de resultados parciales antes de terminar.
- **Subprocesos**: Python lanza y controla el binario C++ vía `subprocess.Popen`.

---

## Arquitectura

```
main.py (Python)
    │
    ├── subprocess.Popen ──► crawler (C++)
    │                            ├── UrlQueue  (mutex + condition_variable)
    │                            └── Worker ×N (pthreads)
    │                                   ├── Fetcher  (libcpr / libcurl)
    │                                   └── stdout ──► JSON por línea
    │
    └── pipe (stdout del subproceso)
            │
            ▼
    processor/
        ├── extractor/   — BeautifulSoup: extrae título y cuerpo de la página
        ├── classifier/  — Detecta habilidades contra data/skills.txt
        ├── analyzer/    — Acumula frecuencias y co-ocurrencias (Counter)
        └── writer/      — Escribe los tres archivos de salida
```

---

## Requisitos

### Sin Docker (Ubuntu 22.04+)

- `g++` ≥ 11
- `python3` ≥ 3.10
- `libcurl4-openssl-dev`, `libssl-dev`
- `libgumbo-dev`
- `nlohmann-json3-dev`
- [libcpr](https://github.com/libcpr/cpr) (compilada desde fuente — ver Instalación)

### Con Docker

- Docker Engine
- Docker Compose

---

## Instalación

### Opción A — Docker (recomendada)

```bash
git clone https://github.com/pangoaguirre/skillmap.git
cd skillmap
docker compose build
```

La imagen compila libcpr en una etapa separada y luego compila el crawler C++. El primer build tarda ~5 minutos; los siguientes son inmediatos gracias al caché de capas.

### Opción B — Local (Ubuntu 22.04+)

```bash
git clone https://github.com/pangoaguirre/skillmap.git
cd skillmap

# Dependencias del sistema
sudo apt install g++ cmake git libcurl4-openssl-dev libssl-dev libgumbo-dev nlohmann-json3-dev

# Compilar libcpr desde fuente
git clone https://github.com/libcpr/cpr.git /tmp/cpr
cmake -B /tmp/cpr/build -S /tmp/cpr -DCPR_USE_SYSTEM_CURL=ON -DCPR_FORCE_OPENSSL_BACKEND=ON
cmake --build /tmp/cpr/build --parallel
sudo cmake --install /tmp/cpr/build

# Compilar el crawler
make

# Dependencias Python
pip3 install -r requirements.txt
```

---

## Uso

### Con Docker

```bash
# Parámetros por defecto (getonboard Colombia, 60 s, 4 workers)
docker compose up

# Personalizado con variables de entorno
SEED_URL="https://co.computrabajo.com/trabajo-de-programador" TIEMPO=120 WORKERS=6 docker compose up
```

### Local

```bash
python3 main.py --url "https://co.computrabajo.com/trabajo-de-programador" --tiempo 60
```

Los resultados quedan en `output/` en ambos casos.

### Argumentos

| Argumento | Default | Descripción |
|---|---|---|
| `--url` | *(requerido)* | URL semilla desde donde arranca el crawler |
| `--tiempo` | `60` | Duración máxima del crawling en segundos |
| `--workers` | `4` | Número de workers concurrentes del crawler C++ |
| `--min-peso` | `2` | Co-ocurrencias con peso menor a este valor se omiten del grafo |
| `--top` | *(todas)* | Limitar el ranking a las N habilidades más frecuentes |

---

## Salidas

| Archivo | Contenido |
|---|---|
| `output/resultados.csv` | Ranking de habilidades con frecuencia absoluta y porcentaje sobre ofertas válidas |
| `output/grafo.json` | Grafo de co-ocurrencias: nodos (habilidades) y aristas (peso = veces que aparecen juntas) |
| `output/apertura.csv` | Por plataforma: páginas vistas, válidas, bloqueadas y tasa de apertura |

### Ejemplo de resultados (`output/resultados.csv`)

```
posicion,habilidad,frecuencia,porcentaje
1,python,132,44.30
2,aws,125,41.95
3,devops,122,40.94
4,sql,114,38.26
5,ci/cd,103,34.56
...
```

### Ejemplo de apertura (`output/apertura.csv`)

```
plataforma,total_vistas,validas,bloqueadas,otras_descartadas,tasa_apertura
getonbrd.com,566,289,0,277,0.5106
linkedin,2,1,0,1,0.5000
youtube.com,2,0,0,2,0.0000
```

Una `tasa_apertura` de `0.0` indica que la plataforma bloqueó o descartó todas las páginas visitadas.

---

## Catálogo de habilidades

El archivo `data/skills.txt` contiene las habilidades que el clasificador detecta. Cada línea es una habilidad; las líneas con `#` son comentarios. El catálogo cubre:

- Lenguajes: Python, JavaScript, TypeScript, Java, Go, Rust, C++, C#, y más
- Frontend: React, Angular, Vue, Svelte, Next.js, Tailwind, y más
- Backend: Django, FastAPI, Spring Boot, NestJS, Laravel, y más
- Bases de datos: PostgreSQL, MongoDB, Redis, MySQL, Elasticsearch, y más
- Cloud / DevOps: AWS, Azure, Google Cloud, Docker, Kubernetes, Terraform, y más
- Datos / ML: TensorFlow, PyTorch, scikit-learn, Pandas, Airflow, y más
- Seguridad: OWASP, pentesting, SIEM, SOC, ciberseguridad
- Prácticas: Scrum, Agile, CI/CD, TDD, microservices, y más

Para agregar una habilidad basta añadir una línea al archivo; no requiere recompilar nada.

---

## Nota sobre robots.txt

El crawler no verifica `robots.txt` por decisión de diseño (scope del proyecto universitario). En producción esto debería implementarse. Algunos sitios como LinkedIn bloquean el scraping activamente (HTTP 403/429); el clasificador los registra en `apertura.csv` como `bloqueadas` y los descarta del análisis.

---

## Equipo

Universidad de Antioquia — Facultad de Ingeniería  
Curso de Sistemas Operativos y Laboratorio — 2026