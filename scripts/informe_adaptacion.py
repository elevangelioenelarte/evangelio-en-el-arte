"""Aplica la adaptación católica a toda la Biblia y resume el resultado.

Uso:
    python scripts/informe_adaptacion.py datos/biblia.json informe_adaptacion.md
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evangelio.adaptacion import _INDICE, adaptar  # noqa: E402
from evangelio.biblia import Biblia  # noqa: E402

RESIDUOS = {
    "Yahvé / Yah / Jehová": r"\bYahv[eé]h?\b|\bYah\b|\bJehov[aá]\b",
    "Hades / Seol": r"\bHades\b|\bSeol\b",
    "el el / al el / de el": r"\b(?:el el|al el|de el Señor|a el Señor|el Señor Señor)\b",
    "Señor, tu Dios sin artículo al abrir": r"(?:^|[.!?] )Señor, (?:tu|su|vuestro|nuestro) Dios",
}


def main() -> int:
    biblia = Biblia.desde_json(sys.argv[1])
    salida = Path(sys.argv[2])
    por_regla: Counter[str] = Counter()
    residuos: Counter[str] = Counter()
    ejemplos_residuo: dict[str, list[str]] = {k: [] for k in RESIDUOS}
    generales: list[tuple[str, str, str]] = []
    pasajes: list[tuple[str, str, str]] = []
    vocativos: list[tuple[str, str, str]] = []
    total = cambiados = 0

    for libro, caps in biblia.libros.items():
        for cap, versos in caps.items():
            for num, texto in versos.items():
                if not texto:
                    continue
                total += 1
                nuevo, cambios = adaptar(libro, cap, num, texto)
                ref = f"{libro} {cap},{num}"
                if cambios:
                    cambiados += 1
                for c in cambios:
                    por_regla["pasaje" if c.regla.startswith("pasaje") else "general"] += 1
                if (libro, cap, num) in _INDICE:
                    pasajes.append((ref, texto, nuevo))
                elif cambios:
                    generales.append((ref, texto, nuevo))
                    if re.search(r"(?:^|[,.!?¡¿«“] ?)Señor,", nuevo) and "Señor," not in texto:
                        vocativos.append((ref, texto, nuevo))
                for nombre, patron in RESIDUOS.items():
                    if re.search(patron, nuevo):
                        residuos[nombre] += 1
                        if len(ejemplos_residuo[nombre]) < 8:
                            ejemplos_residuo[nombre].append(f"{ref}: {nuevo[:200]}")

    L = ["# Informe de adaptación católica", ""]
    L.append(f"Versículos: {total}. Con algún cambio: {cambiados}. "
             f"Cambios generales: {por_regla['general']}. Cambios de pasaje: {por_regla['pasaje']}.")
    L += ["", "## Residuos tras adaptar (deberían ser cero)", ""]
    for nombre in RESIDUOS:
        L.append(f"- **{nombre}**: {residuos[nombre]}")
        L += [f"    - {e}" for e in ejemplos_residuo[nombre]]

    L += ["", "## Reglas de pasaje: antes y después", ""]
    for ref, antes, despues in pasajes:
        marca = "" if antes != despues else " (SIN CAMBIO)"
        L.append(f"- **{ref}**{marca}\n    - antes: {antes[:400]}\n    - después: {despues[:400]}")

    L += ["", "## Muestra de vocativos detectados", ""]
    paso = max(1, len(vocativos) // 45)
    L.append(f"Total: {len(vocativos)}. Se muestra 1 de cada {paso}.")
    for ref, antes, despues in vocativos[::paso][:45]:
        L.append(f"- **{ref}**: {despues[:230]}")

    L += ["", "## Muestra de cambios generales", ""]
    paso = max(1, len(generales) // 45)
    L.append(f"Total: {len(generales)}. Se muestra 1 de cada {paso}.")
    for ref, antes, despues in generales[::paso][:45]:
        L.append(f"- **{ref}**: {despues[:230]}")

    texto = "\n".join(L) + "\n"
    salida.write_text(texto[:64000], encoding="utf-8")
    print(f"Informe escrito en {salida} ({len(texto)} caracteres)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
