import re
import unicodedata
from dataclasses import dataclass
from bs4 import BeautifulSoup  # type: ignore[import]


@dataclass
class PaginaCruda:
    url: str
    html: str
    bloqueado: bool
    error: str


@dataclass
class TextoExtraido:
    url: str
    plataforma: str
    titulo: str
    cuerpo: str      
    bloqueado: bool
    error: str

_DOMINIOS_CONOCIDOS: dict[str, str] = {
    "computrabajo":  "computrabajo",
    "elempleo":      "elempleo",
    "bumeran":       "bumeran",
    "multitrabajos": "multitrabajos",
    "opcionempleo":  "opcionempleo",
    "getonboard":    "getonboard",
    "tecnoempleo":   "tecnoempleo",
    "trabajando":    "trabajando.com",
    "linkedin":      "linkedin",
    "indeed":        "indeed",
    "glassdoor":     "glassdoor",
}


def _detectar_plataforma(url: str) -> str:
    url_lower = url.lower()
    for clave, nombre in _DOMINIOS_CONOCIDOS.items():
        if clave in url_lower:
            return nombre
    m = re.search(r"https?://(?:www\.)?([^/]+)", url_lower)
    return m.group(1) if m else "desconocida"


_SEL_TITULO: list[str] = [
    "h1.job-title", "h1.jobTitle", "h1[data-testid='job-title']",
    ".job-header h1", ".oferta-titulo", "h1.title", "h1",
]

_SEL_CUERPO: list[str] = [
    "[data-testid='job-description']", ".job-description",
    ".descripcion-oferta", ".job-details", ".jobDescriptionContent",
    "section.description", "#job-description", ".offer-description",
    ".vacancy-description", "article", "main",
]

_TAGS_RUIDO: list[str] = [
    "script", "style", "nav", "header", "footer",
    "aside", "form", "noscript", "iframe", "svg",
]


def _normalizar(texto: str) -> str:
    """NFC -> colapsar espacios -> strip."""
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _primer_selector(soup: BeautifulSoup, selectores: list[str]) -> str:
    for sel in selectores:
        el = soup.select_one(sel)
        if el:
            return el.get_text(separator=" ", strip=True)
    return ""


def extraer(pagina: PaginaCruda) -> TextoExtraido:
    resultado = TextoExtraido(
        url=pagina.url,
        plataforma=_detectar_plataforma(pagina.url),
        titulo="",
        cuerpo="",
        bloqueado=pagina.bloqueado,
        error=pagina.error,
    )

    if pagina.bloqueado or pagina.error or len(pagina.html) < 200:
        return resultado

    try:
        soup = BeautifulSoup(pagina.html, "lxml")
    except Exception:
        soup = BeautifulSoup(pagina.html, "html.parser")

    for tag in soup(_TAGS_RUIDO):
        tag.decompose()

    for tag in soup.find_all("div", class_="login-buttons"):
        tag.decompose()

    titulo = _normalizar(_primer_selector(soup, _SEL_TITULO))
    cuerpo  = _normalizar(_primer_selector(soup, _SEL_CUERPO))

    if not cuerpo:
        cuerpo = _normalizar(soup.get_text(separator=" ", strip=True))

    resultado.titulo = titulo
    resultado.cuerpo = f"{titulo} {cuerpo}".strip()
    return resultado
