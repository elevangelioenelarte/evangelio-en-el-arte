"""Biblia en memoria y extracción del texto de una cita."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import usfm
from .citas import Cita, analizar
from .salmos import liturgico_a_hebreo


class TextoNoEncontrado(LookupError):
    """La Biblia no contiene alguno de los versículos pedidos."""


@dataclass(frozen=True)
class Versiculo:
    libro: str
    capitulo: int
    numero: int
    texto: str


class Biblia:
    """Texto bíblico indexado por libro, capítulo y versículo."""

    def __init__(self, libros: dict[str, dict[int, dict[int, str]]]):
        self.libros = libros

    # --- carga -----------------------------------------------------------

    @classmethod
    def desde_zip_usfm(cls, ruta: str | Path) -> "Biblia":
        """Carga el archivo .zip de USFM tal como lo publica eBible."""
        libros: dict[str, dict[int, dict[int, str]]] = {}
        with zipfile.ZipFile(ruta) as z:
            for nombre in sorted(z.namelist()):
                if not nombre.lower().endswith((".usfm", ".sfm")):
                    continue
                codigo, capitulos = usfm.leer_libro(z.read(nombre).decode("utf-8-sig"))
                if codigo and capitulos:
                    libros[codigo] = capitulos
        if not libros:
            raise ValueError(f"No se encontraron libros USFM en {ruta}")
        return cls(libros)

    @classmethod
    def desde_json(cls, ruta: str | Path) -> "Biblia":
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return cls(
            {
                libro: {int(c): {int(v): t for v, t in vs.items()} for c, vs in caps.items()}
                for libro, caps in datos.items()
            }
        )

    def guardar_json(self, ruta: str | Path) -> None:
        Path(ruta).write_text(
            json.dumps(self.libros, ensure_ascii=False, indent=0), encoding="utf-8"
        )

    # --- consulta --------------------------------------------------------

    def _libro_real(self, libro: str, capitulo: int) -> str:
        # Daniel 3 (versión larga), 13 y 14 solo existen en el Daniel griego.
        if libro == "DAN" and capitulo in (3, 13, 14) and "DAG" in self.libros:
            return "DAG"
        return libro

    def versiculos(self, cita: Cita | str, salmo_liturgico: bool = True) -> list[Versiculo]:
        """Devuelve los versículos de una cita, en orden.

        Medio versículo se resuelve tomando el versículo entero. Si la cita es
        un salmo y `salmo_liturgico` es cierto, el número se convierte de la
        numeración litúrgica a la hebrea.
        """
        if isinstance(cita, str):
            cita = analizar(cita)
        salida: list[Versiculo] = []
        for tramo in cita.tramos:
            if cita.libro == "PSA" and salmo_liturgico:
                salida.extend(self._salmo(tramo))
            else:
                salida.extend(
                    self._rango(cita.libro, tramo.cap_ini, tramo.ver_ini, tramo.cap_fin, tramo.ver_fin)
                )
        return salida

    def _salmo(self, tramo) -> list[Versiculo]:
        """Un tramo de salmo citado con numeración litúrgica."""
        if tramo.cap_ini != tramo.cap_fin:
            raise TextoNoEncontrado("Un tramo de salmo no puede cruzar de un salmo a otro")
        partes = liturgico_a_hebreo(tramo.cap_ini)
        if tramo.ver_ini is None:
            salida: list[Versiculo] = []
            for s in partes:
                salida.extend(self._rango("PSA", s.numero, s.ver_ini, s.numero, s.ver_fin))
            return salida
        if len(partes) != 1 or partes[0].ver_ini is not None:
            # Salmos unidos o partidos: los versículos no se corresponden uno a uno.
            raise TextoNoEncontrado(
                f"El salmo litúrgico {tramo.cap_ini} con versículos necesita conversión manual"
            )
        n = partes[0].numero
        return self._rango("PSA", n, tramo.ver_ini, n, tramo.ver_fin)

    def texto(self, cita: Cita | str, salmo_liturgico: bool = True) -> str:
        return " ".join(v.texto for v in self.versiculos(cita, salmo_liturgico) if v.texto)

    def _rango(
        self, libro: str, c1: int, v1: int | None, c2: int, v2: int | None
    ) -> list[Versiculo]:
        salida: list[Versiculo] = []
        for cap in range(c1, c2 + 1):
            real = self._libro_real(libro, cap)
            try:
                versos = self.libros[real][cap]
            except KeyError:
                raise TextoNoEncontrado(f"No está {libro} {cap} en esta Biblia") from None
            primero = v1 if (cap == c1 and v1 is not None) else min(versos)
            ultimo = v2 if (cap == c2 and v2 is not None) else max(versos)
            for n in range(primero, ultimo + 1):
                if n not in versos:
                    raise TextoNoEncontrado(f"No está {libro} {cap},{n} en esta Biblia")
                salida.append(Versiculo(real, cap, n, versos[n]))
        return salida
