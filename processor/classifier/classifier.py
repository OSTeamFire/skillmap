import re
import unicodedata
import logging
from dataclasses import dataclass, field
from pathlib import Path

from processor.extractor import TextoExtraido


logger = logging.getLogger(__name__)

_MIN_CHARS       = 200   
_MIN_RATIO_LATIN = 0.45   

_INDICADORES_TECH: frozenset[str] = frozenset({
    "desarrollador", "developer", "programador", "ingeniero", "software",
    "frontend", "backend", "fullstack", "full stack", "datos", "data",
    "devops", "cloud", "sistemas", "codigo", "code", "api", "base de datos",
    "machine learning", "inteligencia artificial", "ciberseguridad",
    "arquitecto", "tech lead", "scrum", "agile", "repositorio",
    "stack", "framework", "lenguaje", "herramienta", "plataforma",
    "aplicacion", "aplicación", "sistema", "infraestructura",
    "vacante", "oferta", "empleo", "trabajo", "puesto", "cargo",
    "requisito", "requerimiento", "experiencia", "conocimiento",
    "habilidad", "skill", "tecnologia", "tecnología",
})

_PATRONES_RUIDO: list[str] = [
    "403 forbidden", "404 not found", "access denied", "page not found",
    "captcha", "cloudflare", "robot", "inicia sesion", "iniciar sesion",
    "crear cuenta", "politica de privacidad", "terminos y condiciones",
    "resultados de busqueda", "ofertas encontradas",
]

_ALIAS: dict[str, str] = {
    # Lenguajes
    "js":               "javascript",
    "ts":               "typescript",
    "py":               "python",
    "golang":           "go",
    # Node y frameworks
    "nodejs":           "node.js",
    "node":             "node.js",
    "nextjs":           "next.js",
    "nuxtjs":           "nuxt",
    "vuejs":            "vue",
    "reactjs":          "react",
    # Bases de datos
    "postgres":         "postgresql",
    "mongo":            "mongodb",
    "elastic":          "elasticsearch",
    # Cloud
    "gcp":              "google cloud",
    "amazon web services": "aws",
    "microsoft azure":  "azure",
    "aws lambda":       "aws",
    # DevOps
    "k8s":              "kubernetes",
    "cicd":             "ci/cd",
    # ML / Data
    "sklearn":          "scikit-learn",
    "scikit":           "scikit-learn",
    "torch":            "pytorch",
    "tf":               "tensorflow",
    "ia":               "machine learning",
    "inteligencia artificial": "machine learning",
    "ml":               "machine learning",
    "dl":               "deep learning",
    "cv":               "computer vision",
    "nlp":              "nlp",
    # APIs y arquitectura
    "rest":             "api rest",
    "restful":          "api rest",
    "api restful":      "api rest",
    "rest api":         "api rest",
    "microservicio":    "microservices",
    "microservicios":   "microservices",
    # Contenedores
    "contenedor":       "docker",
    "contenedores":     "docker",
    # Control de versiones
    "git hub":          "github",
    "git lab":          "gitlab",
    # Metodologias
    "domain-driven design": "domain driven design",
    "ddd":              "domain driven design",
    "tdd":              "tdd",
    "bdd":              "tdd",
}

# Habilidades cortas que generan muchos falsos positivos si no se delimitan bien
_HABILIDADES_ESTRICTAS: frozenset[str] = frozenset({"r", "c", "go", "c++", "c#"})


def _cargar_catalogo(ruta: Path | None = None) -> list[str]:
    if ruta is None:
        ruta = Path(__file__).parent.parent.parent / "data" / "skills.txt"

    habilidades: list[str] = []
    try:
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip().lower()
            if linea and not linea.startswith("#"):
                habilidades.append(linea)
    except FileNotFoundError:
        logger.warning("No se encontro data/skills.txt — catalogo vacio.")

    habilidades.sort(key=len, reverse=True)
    return habilidades


_CATALOGO: list[str] = _cargar_catalogo()

@dataclass
class OfertaClasificada:
    url: str
    plataforma: str
    titulo: str
    habilidades: list[str] = field(default_factory=list)
    valida: bool = True
    razon_descarte: str = ""


def _ratio_latin(texto: str) -> float:
    if not texto:
        return 0.0
    total = len(texto)
    latinos = sum(
        1 for c in texto
        if unicodedata.category(c).startswith("L")
        and unicodedata.name(c, "").startswith("LATIN")
    )
    return latinos / total


def _es_pagina_ruido(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in _PATRONES_RUIDO)


def _es_oferta_tech(texto: str) -> bool:
    t = texto.lower()
    return any(ind in t for ind in _INDICADORES_TECH)


def _validar(texto: TextoExtraido) -> tuple[bool, str]:
    if texto.bloqueado:
        return False, "bloqueado_403_429"
    if texto.error:
        return False, f"error_red:{texto.error[:60]}"
    if len(texto.cuerpo) < _MIN_CHARS:
        return False, "texto_demasiado_corto"
    if _es_pagina_ruido(texto.cuerpo):
        return False, "pagina_ruido"
    if _ratio_latin(texto.cuerpo) < _MIN_RATIO_LATIN:
        return False, "idioma_no_compatible"
    if not _es_oferta_tech(texto.cuerpo):
        return False, "no_es_oferta_tech"
    return True, ""


def _normalizar_habilidad(h: str) -> str:
    return _ALIAS.get(h, h)


def _detectar_habilidades(texto: str, catalogo: list[str]) -> list[str]:
    texto_norm = unicodedata.normalize("NFC", texto.lower())
    encontradas: set[str] = set()

    for habilidad in catalogo:
        escaped = re.escape(habilidad)

        if habilidad in _HABILIDADES_ESTRICTAS:
            patron = re.compile(
                r"(?<![A-Za-z0-9_.+#])" + escaped + r"(?![A-Za-z0-9_.+#])",
                re.IGNORECASE,
            )
        else:
            try:
                patron = re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)
            except re.error:
                patron = re.compile(
                    r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])",
                    re.IGNORECASE,
                )

        if patron.search(texto_norm):
            encontradas.add(_normalizar_habilidad(habilidad))

    return sorted(encontradas)


def clasificar(texto: TextoExtraido) -> OfertaClasificada:
    resultado = OfertaClasificada(
        url=texto.url,
        plataforma=texto.plataforma,
        titulo=texto.titulo,
    )

    valida, razon = _validar(texto)
    if not valida:
        resultado.valida = False
        resultado.razon_descarte = razon
        logger.debug("Descartada [%s]: %s", razon, texto.url)
        return resultado

    habilidades = _detectar_habilidades(texto.cuerpo, _CATALOGO)

    if not habilidades:
        resultado.valida = False
        resultado.razon_descarte = "sin_habilidades_detectadas"
        logger.debug("Sin habilidades: %s", texto.url)
        return resultado

    resultado.habilidades = habilidades
    return resultado
