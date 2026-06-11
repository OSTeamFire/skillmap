import csv
import json
import logging
from pathlib import Path

from processor.analyzer import SkillMap


logger = logging.getLogger(__name__)

_DIR_SALIDA = Path(__file__).parent.parent.parent / "output"


def _asegurar_directorio(ruta: Path) -> None:
    ruta.mkdir(parents=True, exist_ok=True)


def escribir_ranking(sm: SkillMap, top: int | None = None) -> Path:
    _asegurar_directorio(_DIR_SALIDA)
    ruta = _DIR_SALIDA / "resultados.csv"

    filas = sm.ranking(top=top)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["posicion", "habilidad", "frecuencia", "porcentaje"],
            extrasaction="ignore",
        )
        writer.writeheader()
        for entrada in filas:
            writer.writerow(entrada.to_dict())

    logger.info("Ranking escrito: %s (%d habilidades)", ruta, len(filas))
    return ruta


def escribir_grafo(sm: SkillMap, min_peso: int = 2) -> Path:
    _asegurar_directorio(_DIR_SALIDA)
    ruta = _DIR_SALIDA / "grafo.json"

    grafo = sm.grafo_coocurrencias(min_peso=min_peso)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(grafo, f, ensure_ascii=False, indent=2)

    logger.info(
        "Grafo escrito: %s (%d nodos, %d aristas)",
        ruta, len(grafo["nodos"]), len(grafo["aristas"])
    )
    return ruta


def escribir_apertura(sm: SkillMap) -> Path:
    _asegurar_directorio(_DIR_SALIDA)
    ruta = _DIR_SALIDA / "apertura.csv"

    filas = sm.apertura_plataformas()

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "plataforma", "total_vistas", "validas",
                "bloqueadas", "otras_descartadas", "tasa_apertura",
            ],
        )
        writer.writeheader()
        for entrada in filas:
            writer.writerow(entrada.to_dict())

    logger.info("Apertura escrita: %s (%d plataformas)", ruta, len(filas))
    return ruta


def escribir_todo(sm: SkillMap, top: int | None = None, min_peso: int = 2) -> dict[str, Path]:
    return {
        "resultados": escribir_ranking(sm, top=top),
        "grafo":      escribir_grafo(sm, min_peso=min_peso),
        "apertura":   escribir_apertura(sm),
    }
