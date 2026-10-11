"""Adaptación del vocabulario al uso católico en español.

La Biblia del proyecto es de dominio público, pero no es una traducción
católica: escribe «Yahvé» donde la liturgia dice «el Señor», «Hades» donde
se dice «abismo» o «infierno», «muy favorecida» donde todos conocen «llena
de gracia». Este módulo aplica sustituciones fijas y documentadas.

Principios:
  * Solo reglas deterministas. Ningún modelo reescribe el texto sagrado.
  * Cada cambio queda registrado, para poder revisarlo y explicarlo.
  * Las reglas de pasaje (un versículo concreto) van antes que las generales.

Las reglas salen de la auditoría del texto real
(scripts/auditar_vocabulario.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NT = frozenset(
    "MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS "
    "1PE 2PE 1JN 2JN 3JN JUD REV".split()
)


@dataclass(frozen=True)
class Cambio:
    regla: str
    antes: str
    despues: str


# --- El nombre de Dios -----------------------------------------------------

_NOMBRE = r"(?:Yahv[eé]h?|Yah|Jehov[aá])"
_APOSICION = r"(?:,\s*(?:el |tu |su |mi |nuestro |vuestro )?Dios\b)"
_ABRE = "«“\"‘'¡¿(—– "


def _inicio_de_frase(texto: str, pos: int) -> bool:
    """¿La posición abre una frase? (principio del texto o tras . ! ? :)"""
    previo = texto[:pos].rstrip(_ABRE)
    return not previo or previo[-1] in ".!?:;»”"


def _el_senor(m: re.Match[str]) -> str:
    return "El Señor" if _inicio_de_frase(m.string, m.start()) else "el Señor"


# Tras «Yahvé,» al abrir frase, estas palabras indican que es sujeto y no vocativo:
# «Yahvé, pues, dio a Salomón…», «Yahvé, que hizo los cielos…», «Yahvé, el Dios de…».
_NO_VOCATIVO = r"(?:pues|entonces|que|quien|el|tu|su|vuestro|él|también|además|sin embargo)\b"


def _nombre_de_dios(texto: str) -> str:
    # «Yah, Yahvé» es una sola mención: «el Señor»
    texto = re.sub(r"\bYah,? (Yahv[eé]h?),?", r"\1", texto)
    # «Señor Yahvé» (Adonai YHWH) -> «Señor Dios»
    texto = re.sub(rf"\bSeñor {_NOMBRE}\b", "Señor Dios", texto)
    # «Yahvé de los Ejércitos» y «Señor de los Ejércitos» -> minúscula litúrgica
    texto = re.sub(r"de los Ejércitos", "de los ejércitos", texto)
    # Vocativo con «oh»
    texto = re.sub(rf"\b([Oo])h,? {_NOMBRE}\b", r"\1h Señor", texto)
    # Preposiciones que se contraen
    texto = re.sub(rf"\b([Dd])e {_NOMBRE}\b", r"\1el Señor", texto)
    texto = re.sub(rf"\b([Aa]) {_NOMBRE}\b", r"\1l Señor", texto)
    # Aposición al pronombre: «yo, Yahvé, que os santifico» -> «yo, el Señor,»
    texto = re.sub(rf"\b([Yy]o,\s*){_NOMBRE}\b", r"\1el Señor", texto)
    # Vocativo entre comas o tras coma: «Escucha, Yahvé, mi voz»
    texto = re.sub(rf"(,\s*){_NOMBRE}\b(?!{_APOSICION})(?=\s*[,.;:!?»”])", r"\1Señor", texto)

    # Vocativo al abrir frase: «Yahvé, ¿quién habitará…?» (pero no «Yahvé, tu Dios, …»)
    def _abre(m: re.Match[str]) -> str:
        if not _inicio_de_frase(m.string, m.start()):
            return "el Señor"
        sigue = m.string[m.end():].lstrip(", ")
        return "El Señor" if re.match(_NO_VOCATIVO, sigue) else "Señor"

    texto = re.sub(rf"\b{_NOMBRE}\b(?=,)(?!{_APOSICION})", _abre, texto)
    # Resto de casos
    return re.sub(rf"\b{_NOMBRE}\b", _el_senor, texto)


# --- Reglas generales ------------------------------------------------------

def _generales(libro: str, texto: str) -> str:
    texto = _nombre_de_dios(texto)
    texto = re.sub(r"\b(?:Hades|Seol|Sheol)\b", "abismo", texto)
    texto = re.sub(r"\bElisabeth?\b", "Isabel", texto)
    if libro in NT:
        texto = re.sub(r"\bJacobo\b", "Santiago", texto)
        texto = re.sub(
            r"\b(?:(el|del|al|un|este|ese|aquel) )?(n)uevo (p)acto\b",
            _nueva_alianza,
            texto,
            flags=re.I,
        )
    return texto


_DETERMINANTE_FEMENINO = {
    "el": "la", "del": "de la", "al": "a la", "un": "una",
    "este": "esta", "ese": "esa", "aquel": "aquella",
}


def _nueva_alianza(m: re.Match[str]) -> str:
    """«el nuevo pacto» -> «la nueva alianza», con el determinante en femenino."""
    det, n, p = m.group(1), m.group(2), m.group(3)
    nucleo = ("N" if n.isupper() else "n") + "ueva " + ("A" if p.isupper() else "a") + "lianza"
    if not det:
        return nucleo
    femenino = _DETERMINANTE_FEMENINO[det.lower()]
    if det[0].isupper():
        femenino = femenino[0].upper() + femenino[1:]
    return f"{femenino} {nucleo}"


# --- Reglas de pasaje ------------------------------------------------------
# (libro, capítulo, versículos) -> lista de (patrón, sustitución)

def _vv(*numeros: int | range) -> frozenset[int]:
    salida: set[int] = set()
    for n in numeros:
        salida.update(n if isinstance(n, range) else (n,))
    return frozenset(salida)


def _may(m: re.Match[str], minuscula: str) -> str:
    """Conserva la mayúscula inicial de lo sustituido."""
    return minuscula[0].upper() + minuscula[1:] if m.group(0)[0].isupper() else minuscula


_CALIZ = [
    (r"\b[Dd]e la copa\b", lambda m: _may(m, "del cáliz")),
    (r"\b[Aa] la copa\b", lambda m: _may(m, "al cáliz")),
    (r"\b[Ll]a copa\b", lambda m: _may(m, "el cáliz")),
    (r"\b[Ee]sta copa\b", lambda m: _may(m, "este cáliz")),
    (r"\b[Uu]na copa\b", lambda m: _may(m, "un cáliz")),
    (r"\bcopa\b", "cáliz"),
    (r"\bse la dio\b", "se lo dio"),
    (r"\bde ella\b", "de él"),
    (r"\bla beba\b", "lo beba"),
]

_PRESBITEROS = [(r"\b([Aa])ncianos\b", lambda m: ("P" if m.group(1) == "A" else "p") + "resbíteros"),
                (r"\b([Aa])nciano\b", lambda m: ("P" if m.group(1) == "A" else "p") + "resbítero")]

_BIENAVENTURADOS = [(r"\bBenditos (?:sean|sois|seáis)\b", "Bienaventurados"),
                    (r"\bbenditos (?:sean|sois|seáis)\b", "bienaventurados"),
                    (r"\bDichosos\b", "Bienaventurados"),
                    (r"\bdichosos\b", "bienaventurados")]

_CONVERTIOS = [(r"\bArrepentíos\b", "Convertíos"), (r"\barrepentíos\b", "convertíos")]

_PASAJES: list[tuple[str, int, frozenset[int], list]] = [
    ("LUK", 1, _vv(28), [(r"\bmuy favorecida\b", "llena de gracia")]),
    ("LUK", 2, _vv(14), [(r"en la tierra la paz, la buena voluntad hacia los hombres",
                           "en la tierra paz a los hombres de buena voluntad")]),
    ("MAT", 5, _vv(range(3, 12)), _BIENAVENTURADOS),
    ("LUK", 6, _vv(range(20, 23)), _BIENAVENTURADOS),
    ("MAT", 3, _vv(2), _CONVERTIOS),
    ("MAT", 4, _vv(17), _CONVERTIOS),
    ("MRK", 1, _vv(15), _CONVERTIOS + [(r"\ben la Buena Nueva\b", "en el Evangelio")]),
    ("MAT", 6, _vv(13), [(r"\s*Porque tuyo es el Reino.*?Amén\.?", ""),
                          (r"\bno nos metas en tentación\b", "no nos dejes caer en la tentación")]),
    ("LUK", 11, _vv(4), [(r"\bno nos metas en tentación\b", "no nos dejes caer en la tentación")]),
    ("MAT", 16, _vv(18), [(r"\bHades\b", "infierno")]),
    ("LUK", 16, _vv(23), [(r"\b(?:el |al )?Hades\b", lambda m: "al infierno" if m.group(0).startswith("al") else "el infierno")]),
    ("MAT", 18, _vv(17), [(r"\basamblea\b", "Iglesia")]),
    ("JHN", 14, _vv(16, 26), [(r"\bConsejero\b", "Paráclito")]),
    ("JHN", 15, _vv(26), [(r"\bConsejero\b", "Paráclito")]),
    ("JHN", 16, _vv(7), [(r"\bConsejero\b", "Paráclito")]),
    # El cáliz: última cena, Getsemaní y «¿podéis beber el cáliz?»
    ("MAT", 20, _vv(22, 23), _CALIZ),
    ("MAT", 26, _vv(27, 39, 42), _CALIZ),
    ("MRK", 10, _vv(38, 39), _CALIZ),
    ("MRK", 14, _vv(23, 36), _CALIZ),
    ("LUK", 22, _vv(17, 20, 42), _CALIZ),
    ("JHN", 18, _vv(11), _CALIZ),
    ("1CO", 10, _vv(16, 21), _CALIZ),
    ("1CO", 11, _vv(25, 26, 27, 28), _CALIZ),
    # Presbíteros de la Iglesia
    ("ACT", 11, _vv(30), _PRESBITEROS),
    ("ACT", 14, _vv(23), _PRESBITEROS),
    ("ACT", 15, _vv(2, 4, 6, 22, 23), _PRESBITEROS),
    ("ACT", 16, _vv(4), _PRESBITEROS),
    ("ACT", 20, _vv(17), _PRESBITEROS),
    ("ACT", 21, _vv(18), _PRESBITEROS),
    ("1TI", 5, _vv(17, 19), _PRESBITEROS),
    ("TIT", 1, _vv(5), _PRESBITEROS),
    ("JAS", 5, _vv(14), _PRESBITEROS),
    ("1PE", 5, _vv(1), _PRESBITEROS),
    ("2JN", 1, _vv(1), _PRESBITEROS),
    ("3JN", 1, _vv(1), _PRESBITEROS),
]

_INDICE: dict[tuple[str, int, int], list] = {}
for _libro, _cap, _versos, _reglas in _PASAJES:
    for _v in _versos:
        _INDICE.setdefault((_libro, _cap, _v), []).extend(_reglas)


def _limpiar_espacios(texto: str) -> str:
    return re.sub(r"\s{2,}", " ", texto).strip()


def adaptar(libro: str, capitulo: int, versiculo: int, texto: str) -> tuple[str, list[Cambio]]:
    """Devuelve el texto adaptado y la lista de cambios hechos."""
    cambios: list[Cambio] = []
    actual = texto
    for patron, sustitucion in _INDICE.get((libro, capitulo, versiculo), []):
        nuevo = re.sub(patron, sustitucion, actual, flags=re.S)
        if nuevo != actual:
            cambios.append(Cambio(f"pasaje {libro} {capitulo},{versiculo}", actual, nuevo))
            actual = nuevo
    nuevo = _generales(libro, actual)
    if nuevo != actual:
        cambios.append(Cambio("general", actual, nuevo))
        actual = nuevo
    return _limpiar_espacios(actual), cambios


def adaptar_versiculos(versiculos) -> tuple[str, list[Cambio]]:
    """Adapta una lista de versículos y devuelve el texto unido y sus cambios."""
    partes: list[str] = []
    cambios: list[Cambio] = []
    for v in versiculos:
        if not v.texto:
            continue
        texto, hechos = adaptar(v.libro, v.capitulo, v.numero, v.texto)
        partes.append(texto)
        cambios.extend(hechos)
    return " ".join(partes), cambios
