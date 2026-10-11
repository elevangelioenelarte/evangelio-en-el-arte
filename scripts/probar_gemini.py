"""Comprueba que la clave de Gemini funciona y qué modelos ofrece.

Nunca imprime la clave. Pide la lista de modelos y hace una petición mínima
de texto. Deja el resultado como anotaciones de GitHub Actions.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"


def aviso(titulo: str, mensaje: str, nivel: str = "notice") -> None:
    limpio = mensaje.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::{nivel} title={titulo}::{limpio}")


def pedir(ruta: str, clave: str, cuerpo: dict | None = None) -> tuple[int, dict]:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(
        f"{BASE}/{ruta}",
        data=datos,
        headers={"x-goog-api-key": clave, "Content-Type": "application/json"},
        method="POST" if datos else "GET",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def main() -> int:
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave:
        aviso("Clave de Gemini", "El secreto GEMINI_API_KEY no existe o está vacío.", "error")
        return 1

    estado, datos = pedir("models?pageSize=200", clave)
    if estado != 200:
        mensaje = datos.get("error", {}).get("message", "sin detalle")
        aviso("Clave de Gemini", f"La lista de modelos respondió {estado}: {mensaje}", "error")
        return 1
    nombres = sorted(m["name"].removeprefix("models/") for m in datos.get("models", []))
    interes = [n for n in nombres if any(p in n for p in ("tts", "flash", "image", "lyria", "omni"))]
    aviso("Clave de Gemini", f"Válida. {len(nombres)} modelos disponibles.")
    aviso("Modelos de interés", "\n".join(interes[:60]))

    modelo = os.environ.get("GEMINI_MODELO", "gemini-3.8-flash")
    if modelo not in nombres:
        candidatos = [n for n in nombres if "flash" in n and "tts" not in n and "image" not in n and "live" not in n]
        modelo = candidatos[-1] if candidatos else nombres[0]
    estado, datos = pedir(
        f"models/{modelo}:generateContent",
        clave,
        {"contents": [{"parts": [{"text": "Responde solo con la palabra: listo"}]}]},
    )
    if estado != 200:
        mensaje = datos.get("error", {}).get("message", "sin detalle")
        aviso("Prueba de texto", f"{modelo} respondió {estado}: {mensaje}", "error")
        return 1
    try:
        texto = datos["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        texto = "(respuesta sin texto)"
    aviso("Prueba de texto", f"{modelo} respondió: {texto[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
