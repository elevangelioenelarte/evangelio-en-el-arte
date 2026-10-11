"""Lector de archivos USFM, el formato en que eBible distribuye las Biblias.

Convierte el contenido de un libro en {capítulo: {versículo: texto}}, sin
notas, referencias cruzadas ni títulos de sección.
"""

from __future__ import annotations

import re

# Marcadores cuya línea entera no forma parte del texto bíblico.
_NO_TEXTO = re.compile(
    r"^\\(?:id|ide|usfm|h\d?|toc\d?|toca\d?|mt\d?|mte\d?|ms\d?|mr|s\d?|sr|r|d|sp|sd\d?|"
    r"rem|cl|cp|cd|ca|va|vp|is\d?|ip|ipi|im|imi|ipq|imq|ipr|iq\d?|ib|ili\d?|iot|io\d?|"
    r"iex|imt\d?|imte\d?|ie|lit|restore|periph|qa)\b"
)
# Marcadores de párrafo y poesía: se descartan, pero el texto de la línea se conserva.
_PARRAFO = re.compile(
    r"^\\(?:p|m|po|pr|cls|pmo|pm|pmc|pmr|pi\d?|mi|nb|pc|ph\d?|b|q\d?|qr|qc|qm\d?|qd|"
    r"lh|li\d?|lf|lim\d?|tr|th\d?|thr\d?|tc\d?|tcr\d?)\b\s*"
)
_NOTA = re.compile(r"\\(f|fe|x|ef|ex)\b.*?\\\1\*", re.S)
_FIGURA = re.compile(r"\\fig\b.*?\\fig\*", re.S)
_ATRIBUTOS = re.compile(r"\|[^\\]*?(?=\\)")
_MARCA = re.compile(r"\\\+?[a-z]+\d?\*?")
_VERSICULO = re.compile(r"\\v\s+(\d+)[a-z]?(?:[-,](\d+)[a-z]?)?\s*")


def limpiar(texto: str) -> str:
    """Quita notas, figuras, atributos y marcas de carácter de un texto USFM."""
    texto = _NOTA.sub("", texto)
    texto = _FIGURA.sub("", texto)
    texto = _ATRIBUTOS.sub("", texto)
    texto = _MARCA.sub("", texto)
    return re.sub(r"\s+", " ", texto).strip()


def leer_libro(contenido: str) -> tuple[str | None, dict[int, dict[int, str]]]:
    """Devuelve (código del libro, {capítulo: {versículo: texto}})."""
    codigo: str | None = None
    capitulos: dict[int, dict[int, str]] = {}
    capitulo: int | None = None
    versiculo: int | None = None
    hasta: int | None = None  # último número de un versículo unido, como "1-2"
    trozos: list[str] = []

    def cerrar() -> None:
        if capitulo is not None and versiculo is not None:
            texto = limpiar(" ".join(trozos))
            previo = capitulos[capitulo].get(versiculo)
            capitulos[capitulo][versiculo] = f"{previo} {texto}".strip() if previo else texto
            # En "1-2" el texto queda en el 1; el 2 existe, vacío, para que se pueda citar.
            for n in range(versiculo + 1, (hasta or versiculo) + 1):
                capitulos[capitulo].setdefault(n, "")
        trozos.clear()

    for linea in contenido.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("\\id "):
            partes = linea.split()
            codigo = partes[1].upper() if len(partes) > 1 else None
            continue
        m = re.match(r"^\\c\s+(\d+)", linea)
        if m:
            cerrar()
            capitulo, versiculo, hasta = int(m.group(1)), None, None
            capitulos.setdefault(capitulo, {})
            continue
        if _NO_TEXTO.match(linea):
            continue
        linea = _PARRAFO.sub("", linea)
        # Una línea puede contener varios versículos.
        pos = 0
        for v in _VERSICULO.finditer(linea):
            if v.start() > pos:
                trozos.append(linea[pos:v.start()])
            cerrar()
            versiculo = int(v.group(1))
            hasta = int(v.group(2)) if v.group(2) else None
            pos = v.end()
        if pos < len(linea):
            trozos.append(linea[pos:])
    cerrar()
    return codigo, capitulos
