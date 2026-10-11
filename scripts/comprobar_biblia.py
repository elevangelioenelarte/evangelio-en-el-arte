"""Descarga la Biblia del proyecto y comprueba que las citas de prueba se resuelven.

Uso:
    python scripts/comprobar_biblia.py [carpeta_de_trabajo]

Imprime un resumen (libros, versículos) y el comienzo del texto de cada cita.
Termina con error si la descarga falla o si alguna cita no se encuentra.
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evangelio.biblia import Biblia, TextoNoEncontrado  # noqa: E402

# Santa Biblia libre para el mundo (dominio público), en formato USFM.
URL = os.environ.get("BIBLIA_URL", "https://ebible.org/Scriptures/spablm_usfm.zip")

# Lecturas del domingo 28 del tiempo ordinario, ciclo A, más casos límite.
CITAS = [
    "Is 25,6-10a",
    "Sal 22",
    "Flp 4,12-14.19-20",
    "Mt 22,1-14",
    "Sb 7,7-11",
    "Si 3,17-18.20.28-29",
    "Tb 12,6-13",
    "2M 7,1-2.9-14",
    "Ba 5,1-9",
    "Dn 3,25.34-43",
    "Dn 13,41-62",
]


def aviso(titulo: str, mensaje: str, nivel: str = "notice") -> None:
    """En GitHub Actions deja el dato como anotación, consultable sin abrir el registro."""
    if os.environ.get("GITHUB_ACTIONS"):
        limpio = mensaje.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
        print(f"::{nivel} title={titulo}::{limpio}")


def main() -> int:
    carpeta = Path(sys.argv[1] if len(sys.argv) > 1 else "datos")
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / "biblia_usfm.zip"

    print(f"Descargando {URL}")
    peticion = urllib.request.Request(URL, headers={"User-Agent": "evangelio-en-el-arte"})
    with urllib.request.urlopen(peticion, timeout=120) as r, open(destino, "wb") as f:
        f.write(r.read())
    print(f"Guardado en {destino} ({destino.stat().st_size} bytes)")

    biblia = Biblia.desde_zip_usfm(destino)
    total = sum(len(v) for caps in biblia.libros.values() for v in caps.values())
    print(f"Libros: {len(biblia.libros)} | versículos: {total}")
    print("Códigos:", " ".join(sorted(biblia.libros)))
    aviso(
        "Biblia",
        f"{len(biblia.libros)} libros, {total} versículos, {destino.stat().st_size} bytes. "
        + " ".join(sorted(biblia.libros)),
    )

    fallos = 0
    resueltas = []
    for cita in CITAS:
        try:
            texto = biblia.texto(cita)
        except TextoNoEncontrado as e:
            fallos += 1
            print(f"FALLO  {cita}: {e}")
            aviso(f"Cita no resuelta: {cita}", str(e), "error")
            continue
        print(f"OK     {cita} ({len(texto.split())} palabras): {texto[:160]}...")
        resueltas.append(f"{cita} ({len(texto.split())} palabras): {texto[:150]}")
    for i in range(0, len(resueltas), 4):
        aviso(f"Citas resueltas {i + 1}-{min(i + 4, len(resueltas))}", "\n".join(resueltas[i:i + 4]))

    biblia.guardar_json(carpeta / "biblia.json")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
