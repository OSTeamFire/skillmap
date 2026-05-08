# SkillMap

Análisis de demanda de habilidades tecnológicas en el mercado laboral hispanohablante mediante web crawling concurrente híbrido C++/Python.

## Descripción

SkillMap rastrea ofertas de trabajo tech desde una URL semilla, extrae las habilidades técnicas mencionadas y genera un mapa de frecuencias y co-ocurrencias. Adicionalmente documenta qué plataformas permiten rastreo automatizado y cuáles no.

**Desarrollado como proyecto final del curso de Sistemas Operativos — Universidad de Antioquia.**

## Arquitectura

El sistema tiene dos módulos que se comunican mediante un pipe del sistema operativo:

- **crawler/** — Motor de crawling en C++ con workers concurrentes via pthreads
- **processor/** — Analizador en Python que extrae habilidades y genera resultados

## Requisitos

- Ubuntu 20.04 o superior
- g++ 11 o superior
- Python 3.10 o superior
- libcurl4-openssl-dev
- nlohmann/json

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/usuario/skillmap.git
cd skillmap

# Instalar dependencias del sistema
sudo apt install g++ libcurl4-openssl-dev

# Instalar dependencias Python
pip install -r requirements.txt

# Compilar el motor C++
make -C crawler
```

## Uso

```bash
python main.py --url "https://..." --tiempo 60
```

**Argumentos:**
- `--url` URL semilla desde donde arranca el crawler
- `--tiempo` Duración de la ejecución en segundos

## Salidas

| Archivo | Contenido |
|---|---|
| `output/resultados.csv` | Ranking de habilidades con frecuencias |
| `output/grafo.json` | Grafo de co-ocurrencias para visualización |
| `output/apertura.csv` | Índice de apertura de plataformas |

## Equipo

Universidad de Antioquia — Facultad de Ingeniería  
Curso de Sistemas Operativos y Laboratorio — 2026
