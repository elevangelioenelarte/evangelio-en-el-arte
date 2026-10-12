"""Comprueba el permiso de YouTube con una consulta de solo lectura.

Cambia el refresh token por un token de acceso y pide los datos del canal.
No sube ni modifica nada. Nunca imprime las claves.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def aviso(titulo: str, mensaje: str, nivel: str = "notice") -> None:
    limpio = mensaje.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::{nivel} title={titulo}::{limpio}")


def json_de(peticion: urllib.request.Request) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(peticion, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def token_de_acceso() -> str | None:
    faltan = [n for n in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(n, "").strip()]
    if faltan:
        aviso("Permiso de YouTube", "Faltan los secretos: " + ", ".join(faltan), "error")
        return None
    datos = urllib.parse.urlencode(
        {
            "client_id": os.environ["YT_CLIENT_ID"].strip(),
            "client_secret": os.environ["YT_CLIENT_SECRET"].strip(),
            "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(),
            "grant_type": "refresh_token",
        }
    ).encode()
    estado, respuesta = json_de(urllib.request.Request("https://oauth2.googleapis.com/token", data=datos))
    if estado != 200:
        detalle = respuesta.get("error_description") or respuesta.get("error") or "sin detalle"
        aviso("Permiso de YouTube", f"Google rechazó el refresh token ({estado}): {detalle}", "error")
        return None
    permisos = respuesta.get("scope", "")
    aviso("Permisos concedidos", permisos.replace(" ", "\n"))
    return respuesta["access_token"]


def main() -> int:
    acceso = token_de_acceso()
    if not acceso:
        return 1
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,status,statistics&mine=true"
    estado, datos = json_de(urllib.request.Request(url, headers={"Authorization": f"Bearer {acceso}"}))
    if estado != 200:
        mensaje = datos.get("error", {}).get("message", "sin detalle")
        aviso("Canal de YouTube", f"La consulta respondió {estado}: {mensaje}", "error")
        return 1
    canales = datos.get("items", [])
    if not canales:
        aviso("Canal de YouTube", "El permiso funciona, pero esa cuenta no tiene canal.", "error")
        return 1
    c = canales[0]
    s, st, est = c.get("snippet", {}), c.get("status", {}), c.get("statistics", {})
    aviso(
        "Canal de YouTube",
        f"{s.get('title')} ({s.get('customUrl', 'sin identificador')}), id {c.get('id')}\n"
        f"Vídeos: {est.get('videoCount', '?')} · suscriptores: {est.get('subscriberCount', '?')}\n"
        f"Vídeos largos: {st.get('longUploadsStatus', '?')} · creado para niños: {st.get('madeForKids', '?')}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
