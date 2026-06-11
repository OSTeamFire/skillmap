from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

from processor.classifier import OfertaClasificada


logger = logging.getLogger(__name__)


@dataclass
class EntradaRanking:
    posicion: int
    habilidad: str
    frecuencia: int                       
    porcentaje: float                     
    plataformas: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "posicion":    self.posicion,
            "habilidad":   self.habilidad,
            "frecuencia":  self.frecuencia,
            "porcentaje":  round(self.porcentaje, 2),
            "plataformas": self.plataformas,
        }


@dataclass
class EntradaApertura:
    plataforma: str
    total_vistas: int    
    validas: int         
    bloqueadas: int       
    otras_descartadas: int

    @property
    def tasa_apertura(self) -> float:
        if self.total_vistas == 0:
            return 0.0
        return round(self.validas / self.total_vistas, 4)

    def to_dict(self) -> dict:
        return {
            "plataforma":        self.plataforma,
            "total_vistas":      self.total_vistas,
            "validas":           self.validas,
            "bloqueadas":        self.bloqueadas,
            "otras_descartadas": self.otras_descartadas,
            "tasa_apertura":     self.tasa_apertura,
        }


class SkillMap:

    def __init__(self) -> None:
        self._freq: Counter[str] = Counter()

        self._freq_plataforma: dict[str, Counter[str]] = {}

        self._cooc: Counter[tuple[str, str]] = Counter()

        self._vistas:     Counter[str] = Counter()   
        self._validas:    Counter[str] = Counter()  
        self._bloqueadas: Counter[str] = Counter()  

        self.total_procesadas: int = 0
        self.total_validas: int = 0
        self.total_descartadas: int = 0
        self._razones_descarte: Counter[str] = Counter()



    def agregar(self, oferta: OfertaClasificada) -> None:

        self.total_procesadas += 1
        plataforma = oferta.plataforma
        self._vistas[plataforma] += 1

        if not oferta.valida:
            self.total_descartadas += 1
            self._razones_descarte[oferta.razon_descarte] += 1
            if "bloqueado" in oferta.razon_descarte:
                self._bloqueadas[plataforma] += 1
            return

        self.total_validas += 1
        self._validas[plataforma] += 1

        skills = oferta.habilidades

        for skill in skills:
            self._freq[skill] += 1
            if skill not in self._freq_plataforma:
                self._freq_plataforma[skill] = Counter()
            self._freq_plataforma[skill][plataforma] += 1

        if len(skills) >= 2:
            for a, b in combinations(sorted(skills), 2):
                self._cooc[(a, b)] += 1

        logger.debug(
            "[%s] %d habilidades | %s",
            plataforma, len(skills), oferta.url
        )

    def ranking(self, top: int | None = None) -> list[EntradaRanking]:
        if self.total_validas == 0:
            return []

        ordenadas = self._freq.most_common(top)
        resultado = []
        for pos, (habilidad, freq) in enumerate(ordenadas, start=1):
            resultado.append(EntradaRanking(
                posicion=pos,
                habilidad=habilidad,
                frecuencia=freq,
                porcentaje=freq / self.total_validas * 100,
                plataformas=dict(self._freq_plataforma.get(habilidad, {})),
            ))
        return resultado

    def grafo_coocurrencias(self, min_peso: int = 2) -> dict:
        nodos_activos: set[str] = set()
        aristas = []

        for (a, b), peso in self._cooc.items():
            if peso >= min_peso:
                aristas.append({"fuente": a, "destino": b, "peso": peso})
                nodos_activos.add(a)
                nodos_activos.add(b)

        aristas.sort(key=lambda e: e["peso"], reverse=True)

        nodos = [
            {
                "id":         n,
                "frecuencia": self._freq.get(n, 0),
            }
            for n in sorted(nodos_activos)
        ]

        return {
            "nodos":   nodos,
            "aristas": aristas,
            "meta": {
                "total_ofertas":   self.total_procesadas,
                "ofertas_validas": self.total_validas,
                "min_peso":        min_peso,
                "total_nodos":     len(nodos),
                "total_aristas":   len(aristas),
            },
        }

    def apertura_plataformas(self) -> list[EntradaApertura]:
        todas = set(self._vistas.keys())
        resultado = []

        for plataforma in sorted(todas):
            vistas    = self._vistas[plataforma]
            validas   = self._validas[plataforma]
            bloqueadas = self._bloqueadas[plataforma]
            otras     = vistas - validas - bloqueadas

            resultado.append(EntradaApertura(
                plataforma=plataforma,
                total_vistas=vistas,
                validas=validas,
                bloqueadas=bloqueadas,
                otras_descartadas=max(otras, 0),
            ))

        resultado.sort(key=lambda e: e.tasa_apertura, reverse=True)
        return resultado

    def resumen(self) -> dict:
        return {
            "total_procesadas":   self.total_procesadas,
            "total_validas":      self.total_validas,
            "total_descartadas":  self.total_descartadas,
            "habilidades_unicas": len(self._freq),
            "pares_coocurrencia": len(self._cooc),
            "razones_descarte":   dict(self._razones_descarte),
        }
