"""Control de fidelidad: la narración debe coincidir con el texto bíblico.

Dos usos:
  * exacto: el guion que se envía a la voz frente al texto extraído de la
    Biblia. Tiene que coincidir palabra por palabra.
  * aproximado: la transcripción del audio final frente al texto. El
    reconocimiento de voz comete errores propios, así que se exige una
    similitud mínima en lugar de identidad.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

UMBRAL_TRANSCRIPCION = 0.97


@dataclass(frozen=True)
class Diferencia:
    tipo: str  # "cambia", "falta" o "sobra"
    esperado: str
    obtenido: str


@dataclass(frozen=True)
class Resultado:
    similitud: float
    diferencias: tuple[Diferencia, ...] = field(default_factory=tuple)

    @property
    def exacto(self) -> bool:
        return not self.diferencias

    def aprobado(self, umbral: float = 1.0) -> bool:
        return self.similitud >= umbral


def palabras(texto: str) -> list[str]:
    """Palabras del texto en minúsculas, sin puntuación. Los acentos se conservan."""
    texto = unicodedata.normalize("NFC", texto).lower()
    return re.findall(r"[^\W_]+", texto)


def comparar(esperado: str, obtenido: str) -> Resultado:
    """Compara dos textos palabra por palabra."""
    a, b = palabras(esperado), palabras(obtenido)
    emparejador = difflib.SequenceMatcher(None, a, b, autojunk=False)
    nombres = {"replace": "cambia", "delete": "falta", "insert": "sobra"}
    diferencias = tuple(
        Diferencia(nombres[op], " ".join(a[i1:i2]), " ".join(b[j1:j2]))
        for op, i1, i2, j1, j2 in emparejador.get_opcodes()
        if op != "equal"
    )
    similitud = 1.0 if not a and not b else emparejador.ratio()
    return Resultado(similitud, diferencias)


def guion_fiel(texto_biblico: str, guion: str) -> Resultado:
    """El guion de narración debe ser idéntico, palabra por palabra, al texto."""
    return comparar(texto_biblico, guion)


def audio_fiel(texto_biblico: str, transcripcion: str, umbral: float = UMBRAL_TRANSCRIPCION) -> bool:
    """La transcripción del audio debe parecerse lo suficiente al texto."""
    return comparar(texto_biblico, transcripcion).aprobado(umbral)
