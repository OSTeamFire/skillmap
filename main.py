import argparse
import json
import logging
import signal
import subprocess
import sys
from pathlib import Path

from processor.extractor import PaginaCruda, extraer
from processor.classifier import clasificar
from processor.analyzer import SkillMap
from processor.writer import escribir_todo


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


_CRAWLER_BIN = Path(__file__).parent / "crawler" / "build" / "crawler"


def _leer_linea_json(linea: str) -> PaginaCruda | None:
    linea = linea.strip()
    if not linea:
        return None
    try:
        datos = json.loads(linea)
        return PaginaCruda(
            url=datos.get("url", ""),
            html=datos.get("html", ""),
            bloqueado=datos.get("bloqueado", False),
            error=datos.get("error", ""),
        )
    except json.JSONDecodeError:
        logger.warning("Linea JSON invalida ignorada: %s", linea[:80])
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SkillMap — analisis de habilidades tech en ofertas laborales"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL semilla desde donde arranca el crawler",
    )
    parser.add_argument(
        "--tiempo",
        type=int,
        default=60,
        help="Duracion maxima del crawling en segundos (default: 60)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Numero de workers concurrentes del crawler C++ (default: 4)",
    )
    parser.add_argument(
        "--min-peso",
        type=int,
        default=2,
        dest="min_peso",
        help="Peso minimo de co-ocurrencia para incluirla en el grafo (default: 2)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Limitar el ranking a las N habilidades mas frecuentes",
    )
    args = parser.parse_args()

    if not _CRAWLER_BIN.exists():
        logger.error(
            "Binario del crawler no encontrado en %s. "
            "Ejecuta 'make -C crawler' primero.",
            _CRAWLER_BIN,
        )
        sys.exit(1)

    skillmap = SkillMap()

    def _shutdown(signum, frame):
        logger.info("Interrupcion recibida — guardando resultados parciales...")
        _guardar_y_salir(skillmap, args)

    signal.signal(signal.SIGINT, _shutdown)

    # Lanzar el crawler C++ como subproceso
    cmd = [
        str(_CRAWLER_BIN),
        "--url",     args.url,
        "--tiempo",  str(args.tiempo),
        "--workers", str(args.workers),
    ]
    logger.info("Iniciando crawler: %s", " ".join(cmd))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,         
        )
    except OSError as e:
        logger.error("No se pudo lanzar el crawler: %s", e)
        sys.exit(1)

    paginas_recibidas = 0
    try:
        for linea in proc.stdout:
            pagina = _leer_linea_json(linea)
            if pagina is None:
                continue

            paginas_recibidas += 1
            texto  = extraer(pagina)
            oferta = clasificar(texto)
            skillmap.agregar(oferta)

            if paginas_recibidas % 50 == 0:
                resumen = skillmap.resumen()
                logger.info(
                    "Progreso: %d recibidas | %d validas | %d habilidades unicas",
                    paginas_recibidas,
                    resumen["total_validas"],
                    resumen["habilidades_unicas"],
                )

    except KeyboardInterrupt:
        pass
    finally:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    logger.info(
        "Crawler finalizado. Total recibidas: %d", paginas_recibidas
    )
    _guardar_y_salir(skillmap, args)


def _guardar_y_salir(skillmap: SkillMap, args: argparse.Namespace) -> None:
    """Escribe los tres archivos de salida y muestra el resumen final."""
    resumen = skillmap.resumen()

    if resumen["total_validas"] == 0:
        logger.warning(
            "No se procesaron ofertas validas. "
            "Verifica la URL semilla y que el crawler este compilado."
        )
        sys.exit(0)

    rutas = escribir_todo(skillmap, top=args.top, min_peso=args.min_peso)

    logger.info("=" * 55)
    logger.info("RESUMEN FINAL")
    logger.info("  Paginas procesadas : %d", resumen["total_procesadas"])
    logger.info("  Ofertas validas    : %d", resumen["total_validas"])
    logger.info("  Descartadas        : %d", resumen["total_descartadas"])
    logger.info("  Habilidades unicas : %d", resumen["habilidades_unicas"])
    logger.info("  Pares co-ocurrencia: %d", resumen["pares_coocurrencia"])
    logger.info("ARCHIVOS GENERADOS")
    for nombre, ruta in rutas.items():
        logger.info("  %-12s -> %s", nombre, ruta)
    logger.info("=" * 55)

    top10 = skillmap.ranking(top=10)
    if top10:
        logger.info("TOP 10 HABILIDADES")
        for e in top10:
            logger.info(
                "  %2d. %-25s %4d ofertas  (%.1f%%)",
                e.posicion, e.habilidad, e.frecuencia, e.porcentaje,
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
