"""Localiza en nuestra Biblia el pasaje que corresponde a un texto guía.

El leccionario cita con la numeración católica. Nuestra Biblia numera algunos
pasajes de otra manera (Isaías 9, Joel, Malaquías, los salmos con título…).
En vez de mantener tablas de conversión, se usa como guía el texto de la
lectura en otra traducción: se parte de la posición que indica la cita y se
prueba a desplazarla unos versículos hasta que nuestro texto es el que más se
parece a la guía.

El texto guía solo sirve para localizar. Nunca se narra ni se publica.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .adaptacion import adaptar
from .biblia import Biblia, TextoNoEncontrado, Versiculo
from .citas import Cita, analizar

VENTANA = 45  # versículos que se prueba a desplazar en cada sentido
SIMILITUD_MINIMA = 0.30  # por debajo, la localización no se considera fiable

_VACIAS = frozenset(
    """a al algo ante aquel aquella aquellos asi aun aunque bien cada como con contra cual
    cuando de del desde donde dos e el ella ellas ellos en entre era eran es esa ese eso esta
    estaba estan este esto estos fue ha habia han has hasta hay he la las le les lo los mas
    me mi mis mismo muy ni no nos nosotros nuestra nuestro o os otra otro para pero por porque
    pues que quien se sea ser si sin sino sobre son su sus tambien te ti tu tus un una uno
    unos vosotros vuestra vuestro y ya yo oh he aqui""".split()
)


def fichas(texto: str) -> set[str]:
    """Palabras con contenido, sin acentos y recortadas a su raíz aproximada."""
    plano = unicodedata.normalize("NFD", texto.lower())
    plano = "".join(c for c in plano if unicodedata.category(c) != "Mn")
    salida = set()
    for palabra in re.findall(r"[a-zñ]+", plano):
        if len(palabra) < 3 or palabra in _VACIAS:
            continue
        salida.add(palabra[:5])
    return salida


def _texto(v: Versiculo) -> str:
    """Texto del versículo tal como se narrará, que es el que se compara con la guía."""
    return adaptar(v.libro, v.capitulo, v.numero, v.texto)[0] if v.texto else ""


def parecido(a: set[str], b: set[str]) -> float:
    """Coeficiente de Dice entre dos conjuntos de fichas."""
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


@dataclass(frozen=True)
class Localizacion:
    versiculos: tuple[Versiculo, ...]
    desplazamiento: int  # versículos movidos respecto a la cita; 0 = numeración igual
    similitud: float
    similitud_sin_mover: float

    @property
    def fiable(self) -> bool:
        return self.similitud >= SIMILITUD_MINIMA

    @property
    def referencia(self) -> str:
        """Dónde está el pasaje en nuestra Biblia, por si difiere de la cita."""
        if not self.versiculos:
            return ""
        a, b = self.versiculos[0], self.versiculos[-1]
        return f"{a.libro} {a.capitulo},{a.numero}-{b.capitulo},{b.numero}"


def _lineal(biblia: Biblia, libro: str) -> list[Versiculo]:
    try:
        capitulos = biblia.libros[libro]
    except KeyError:
        raise TextoNoEncontrado(f"No está el libro {libro} en esta Biblia") from None
    return [
        Versiculo(libro, cap, num, capitulos[cap][num])
        for cap in sorted(capitulos)
        for num in sorted(capitulos[cap])
    ]


def _inicio_de_capitulo(lineal: list[Versiculo], capitulo: int) -> int:
    for i, v in enumerate(lineal):
        if v.capitulo == capitulo:
            return i
    return len(lineal)  # capítulo que no existe aquí: justo después del final


def _posicion(lineal: list[Versiculo], capitulo: int, versiculo: int) -> int:
    """Posición nominal de capítulo y versículo, aunque el número no exista aquí."""
    inicio = _inicio_de_capitulo(lineal, capitulo)
    primero = lineal[inicio].numero if inicio < len(lineal) else 1
    return inicio + (versiculo - primero)


def _fin_de_capitulo(lineal: list[Versiculo], capitulo: int) -> int:
    ultimo = _inicio_de_capitulo(lineal, capitulo)
    while ultimo + 1 < len(lineal) and lineal[ultimo + 1].capitulo == capitulo:
        ultimo += 1
    return ultimo


# Salmos litúrgicos que no se corresponden uno a uno con un salmo hebreo:
# (salmo hebreo donde empieza, versículos que hay que saltar dentro de él)
_SALMOS_PARTIDOS = {9: (9, 0), 113: (114, 0), 114: (116, 0), 115: (116, 9), 146: (147, 0), 147: (147, 11)}


def _tramos_nominales(biblia: Biblia, cita: Cita) -> tuple[list[Versiculo], list[tuple[int, int]]]:
    """Lista lineal del libro y posiciones (inicio, fin) de cada tramo de la cita."""
    if cita.libro == "PSA":
        lineal = _lineal(biblia, "PSA")
        tramos = []
        for t in cita.tramos:
            if t.cap_ini in _SALMOS_PARTIDOS:
                hebreo, salto = _SALMOS_PARTIDOS[t.cap_ini]
            else:
                hebreo, salto = (t.cap_ini if t.cap_ini <= 8 or t.cap_ini >= 148 else t.cap_ini + 1), 0
            base = _inicio_de_capitulo(lineal, hebreo) + salto
            if t.ver_ini is None:
                tramos.append((base, _fin_de_capitulo(lineal, hebreo)))
            else:
                tramos.append((base + t.ver_ini - 1, base + (t.ver_fin or t.ver_ini) - 1))
        return lineal, tramos

    real = biblia._libro_real(cita.libro, cita.tramos[0].cap_ini)
    lineal = _lineal(biblia, real)
    tramos = []
    for t in cita.tramos:
        if t.ver_ini is None:
            tramos.append((_inicio_de_capitulo(lineal, t.cap_ini), _fin_de_capitulo(lineal, t.cap_fin)))
        else:
            tramos.append(
                (_posicion(lineal, t.cap_ini, t.ver_ini), _posicion(lineal, t.cap_fin, t.ver_fin or t.ver_ini))
            )
    return lineal, tramos


def _tomar(lineal: list[Versiculo], tramos: list[tuple[int, int]], k: int) -> list[Versiculo] | None:
    salida: list[Versiculo] = []
    for ini, fin in tramos:
        ini, fin = ini + k, fin + k
        if ini < 0 or fin >= len(lineal) or fin < ini:
            return None
        salida.extend(lineal[ini:fin + 1])
    return salida


def localizar(biblia: Biblia, cita: Cita | str, guia: str, ventana: int = VENTANA) -> Localizacion:
    """Devuelve los versículos de nuestra Biblia que corresponden a la cita y a la guía."""
    if isinstance(cita, str):
        cita = analizar(cita)
    lineal, tramos = _tramos_nominales(biblia, cita)
    objetivo = fichas(guia)

    def puntuar(k: int) -> tuple[float, list[Versiculo] | None]:
        versos = _tomar(lineal, tramos, k)
        if versos is None:
            return -1.0, None
        return parecido(fichas(" ".join(_texto(v) for v in versos)), objetivo), versos

    sin_mover, versos0 = puntuar(0)
    mejor_k, mejor, mejores = 0, sin_mover, versos0
    # Se prueban primero los desplazamientos pequeños; a igualdad gana el menor.
    for distancia in range(1, ventana + 1):
        for k in (-distancia, distancia):
            nota, versos = puntuar(k)
            if nota > mejor + 0.02:
                mejor_k, mejor, mejores = k, nota, versos
    if mejores is None:
        raise TextoNoEncontrado(f"No se pudo localizar {cita.original} en esta Biblia")
    return Localizacion(tuple(mejores), mejor_k, mejor, max(sin_mover, 0.0))


_CORTE = re.compile(r"[.;:!?¡¿]+")
_SALTO_GUIA = 0.12  # coste de dejar sin emparejar una frase de la guía (el estribillo, por ejemplo)
_PESO_LONGITUD = 0.18  # cuánto cuenta que las dos frases midan parecido


def _frases(texto: str) -> list[tuple[set[str], int]]:
    """Frases de un texto como (fichas, número de palabras)."""
    salida = []
    for trozo in _CORTE.split(texto):
        palabras = len(re.findall(r"\w+", trozo))
        if palabras >= 2:
            salida.append((fichas(trozo), palabras))
    return salida


def _nota(a: tuple[set[str], int], b: tuple[set[str], int]) -> float:
    longitud = 1 - abs(a[1] - b[1]) / max(a[1], b[1])
    return parecido(a[0], b[0]) + _PESO_LONGITUD * longitud


def _unir(x: tuple[set[str], int], y: tuple[set[str], int]) -> tuple[set[str], int]:
    return x[0] | y[0], x[1] + y[1]


def versiculos_del_salmo(biblia: Biblia, numero_liturgico: int, guia: str) -> Localizacion:
    """Elige los versículos del salmo que se leen, a partir del texto guía.

    El leccionario lee solo algunas estrofas de cada salmo y la fuente no dice
    cuáles. Se alinean en orden las frases de la guía con las frases del salmo:
    cada frase de la guía busca su lugar, las frases del salmo pueden quedar sin
    pareja y los versículos con alguna frase emparejada son los que se leen.
    """
    lineal, tramos = _tramos_nominales(biblia, analizar(f"Sal {numero_liturgico}"))
    ini, fin = tramos[0]
    candidatos = lineal[ini:fin + 1]
    nuestras: list[tuple[set[str], int]] = []
    dueno: list[int] = []  # a qué versículo pertenece cada frase nuestra
    for i, v in enumerate(candidatos):
        for frase in _frases(_texto(v)):
            nuestras.append(frase)
            dueno.append(i)
    guias = _frases(guia)
    if not nuestras or not guias:
        return Localizacion((), 0, 0.0, 0.0)

    n, m = len(guias), len(nuestras)
    menos = float("-inf")
    mejor = [[menos] * (m + 1) for _ in range(n + 1)]
    paso: list[list[tuple[int, int, bool] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    for k in range(m + 1):
        mejor[0][k] = 0.0
    for i in range(1, n + 1):
        for k in range(0, m + 1):
            opciones: list[tuple[float, tuple[int, int, bool]]] = []
            opciones.append((mejor[i - 1][k] - _SALTO_GUIA, (i - 1, k, False)))  # frase de la guía sin pareja
            if k >= 1:
                opciones.append((mejor[i][k - 1], (i, k - 1, False)))  # frase nuestra que no se lee
                opciones.append((mejor[i - 1][k - 1] + _nota(guias[i - 1], nuestras[k - 1]), (i - 1, k - 1, True)))
            if k >= 2:  # una frase de la guía equivale a dos nuestras
                opciones.append(
                    (mejor[i - 1][k - 2] + _nota(guias[i - 1], _unir(nuestras[k - 2], nuestras[k - 1])), (i - 1, k - 2, True))
                )
            if i >= 2 and k >= 1:  # dos frases de la guía equivalen a una nuestra
                opciones.append(
                    (mejor[i - 2][k - 1] + _nota(_unir(guias[i - 2], guias[i - 1]), nuestras[k - 1]), (i - 2, k - 1, True))
                )
            mejor[i][k], paso[i][k] = max(opciones, key=lambda o: o[0])

    leidos: set[int] = set()
    i, k = n, m
    while i > 0:
        anterior = paso[i][k]
        if anterior is None:
            break
        pi, pk, emparejado = anterior
        if emparejado:
            leidos.update(dueno[pk:k])
        i, k = pi, pk
    elegidos = [v for j, v in enumerate(candidatos) if j in leidos]
    if not elegidos:
        return Localizacion((), 0, 0.0, 0.0)
    nota = parecido(fichas(" ".join(_texto(v) for v in elegidos)), fichas(guia))
    return Localizacion(tuple(elegidos), 0, nota, nota)
