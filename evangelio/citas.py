"""Analizador de citas bíblicas tal como las escribe el leccionario en español.

Ejemplos admitidos:
    Mt 22,1-14              un tramo dentro de un capítulo
    Flp 4,12-14.19-20       varios tramos del mismo capítulo
    Is 25,6-10a             medio versículo: se toma el versículo entero
    Jn 18,1-19,42           tramo que cruza capítulos
    Gn 2,7-9; 3,1-7         tramos en capítulos distintos
    Sal 22                  capítulo completo
    Flm 7-20                libro de un solo capítulo
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


class CitaInvalida(ValueError):
    """La cita no se puede interpretar."""


# Abreviaturas del leccionario -> código USFM del libro.
_LIBROS = {
    "GEN": "gn gen genesis",
    "EXO": "ex exo exodo",
    "LEV": "lv lev levitico",
    "NUM": "nm num numeros",
    "DEU": "dt deut deuteronomio",
    "JOS": "jos josue",
    "JDG": "jue jc jueces",
    "RUT": "rt rut",
    "1SA": "1s 1sm 1sam 1samuel",
    "2SA": "2s 2sm 2sam 2samuel",
    "1KI": "1r 1re 1reyes",
    "2KI": "2r 2re 2reyes",
    "1CH": "1cro 1cr 1cronicas",
    "2CH": "2cro 2cr 2cronicas",
    "EZR": "esd esdras",
    "NEH": "ne neh nehemias",
    "TOB": "tb tob tobias tobit",
    "JDT": "jdt judit",
    "EST": "est ester",
    "1MA": "1m 1mac 1macabeos",
    "2MA": "2m 2mac 2macabeos",
    "JOB": "jb job",
    "PSA": "sal salmo salmos",
    "PRO": "pr prov proverbios",
    "ECC": "ecl qo qoh eclesiastes qohelet",
    "SNG": "ct cant cantar",
    "WIS": "sb sab sabiduria",
    "SIR": "si sir eclo eclesiastico siracida",
    "ISA": "is isa isaias",
    "JER": "jr jer jeremias",
    "LAM": "lm lam lamentaciones",
    "BAR": "ba bar baruc",
    "EZK": "ez ezequiel",
    "DAN": "dn dan daniel",
    "HOS": "os oseas",
    "JOL": "jl joel",
    "AMO": "am amos",
    "OBA": "abd abdias",
    "JON": "jon jonas",
    "MIC": "mi miq miqueas",
    "NAM": "na nah nahum",
    "HAB": "ha hab habacuc",
    "ZEP": "so sof sofonias",
    "HAG": "ag ageo",
    "ZEC": "za zac zacarias",
    "MAL": "ml mal malaquias",
    "MAT": "mt mateo",
    "MRK": "mc mr marcos",
    "LUK": "lc lucas",
    "JHN": "jn juan",
    "ACT": "hch hech hechos",
    "ROM": "rm rom romanos",
    "1CO": "1co 1cor 1corintios",
    "2CO": "2co 2cor 2corintios",
    "GAL": "ga gal galatas",
    "EPH": "ef efesios",
    "PHP": "flp fil filipenses",
    "COL": "col colosenses",
    "1TH": "1ts 1tes 1tesalonicenses",
    "2TH": "2ts 2tes 2tesalonicenses",
    "1TI": "1tm 1tim 1timoteo",
    "2TI": "2tm 2tim 2timoteo",
    "TIT": "tt tit tito",
    "PHM": "flm filemon",
    "HEB": "hb heb hebreos",
    "JAS": "st sant santiago",
    "1PE": "1p 1pe 1pedro",
    "2PE": "2p 2pe 2pedro",
    "1JN": "1jn 1juan",
    "2JN": "2jn 2juan",
    "3JN": "3jn 3juan",
    "JUD": "jds judas",
    "REV": "ap apoc apocalipsis",
}

_ALIAS = {alias: codigo for codigo, nombres in _LIBROS.items() for alias in nombres.split()}

# Libros con un solo capítulo: "Flm 7-20" son versículos, no capítulos.
UN_CAPITULO = {"OBA", "PHM", "2JN", "3JN", "JUD"}

_TROZO = re.compile(
    r"^(?:(?P<c1>\d+),)?(?P<v1>\d+)(?P<l1>[a-d]?)"
    r"(?:-(?:(?P<c2>\d+),)?(?P<v2>\d+)(?P<l2>[a-d]?))?$"
)


@dataclass(frozen=True)
class Tramo:
    """Un tramo continuo de versículos. Sin versículos = capítulo entero."""

    cap_ini: int
    ver_ini: int | None
    cap_fin: int
    ver_fin: int | None
    parcial: bool = False  # la cita pedía medio versículo (10a, 3b...)


@dataclass(frozen=True)
class Cita:
    libro: str  # código USFM
    tramos: tuple[Tramo, ...] = field(default_factory=tuple)
    original: str = ""

    @property
    def tiene_parciales(self) -> bool:
        return any(t.parcial for t in self.tramos)


def _sin_acentos(texto: str) -> str:
    plano = unicodedata.normalize("NFD", texto)
    return "".join(c for c in plano if unicodedata.category(c) != "Mn")


def codigo_libro(nombre: str) -> str:
    """Devuelve el código USFM de una abreviatura o nombre de libro."""
    clave = _sin_acentos(nombre).lower().replace(".", "").replace(" ", "")
    try:
        return _ALIAS[clave]
    except KeyError:
        raise CitaInvalida(f"Libro desconocido: {nombre!r}") from None


def analizar(cita: str) -> Cita:
    """Convierte el texto de una cita en una estructura con sus tramos."""
    original = cita.strip()
    texto = original.replace("–", "-").replace("—", "-").replace("−", "-")
    m = re.match(r"^((?:[1-3]\s*)?[^\W\d_]+)\.?\s*(.*)$", texto)
    if not m:
        raise CitaInvalida(f"No se reconoce la cita: {original!r}")
    libro = codigo_libro(m.group(1))
    resto = re.sub(r"\s+", "", m.group(2))
    if not resto:
        raise CitaInvalida(f"La cita no indica capítulo: {original!r}")

    tramos: list[Tramo] = []
    for grupo in resto.split(";"):
        if not grupo:
            continue
        capitulo: int | None = 1 if libro in UN_CAPITULO else None
        if "," not in grupo and capitulo is None:
            tramos.extend(_capitulos_enteros(grupo, original))
            continue
        for trozo in grupo.split("."):
            t = _TROZO.match(trozo)
            if not t:
                raise CitaInvalida(f"Tramo no reconocido {trozo!r} en {original!r}")
            if t["c1"]:
                capitulo = int(t["c1"])
            if capitulo is None:
                raise CitaInvalida(f"Falta el capítulo en {original!r}")
            v1 = int(t["v1"])
            c2 = int(t["c2"]) if t["c2"] else capitulo
            v2 = int(t["v2"]) if t["v2"] else v1
            if (c2, v2) < (capitulo, v1):
                raise CitaInvalida(f"Tramo al revés {trozo!r} en {original!r}")
            tramos.append(Tramo(capitulo, v1, c2, v2, bool(t["l1"] or t["l2"])))
            capitulo = c2
    if not tramos:
        raise CitaInvalida(f"La cita no tiene tramos: {original!r}")
    return Cita(libro, tuple(tramos), original)


def _capitulos_enteros(grupo: str, original: str) -> list[Tramo]:
    m = re.match(r"^(\d+)(?:-(\d+))?$", grupo)
    if not m:
        raise CitaInvalida(f"Tramo no reconocido {grupo!r} en {original!r}")
    ini = int(m.group(1))
    fin = int(m.group(2)) if m.group(2) else ini
    if fin < ini:
        raise CitaInvalida(f"Capítulos al revés en {original!r}")
    return [Tramo(c, None, c, None) for c in range(ini, fin + 1)]
