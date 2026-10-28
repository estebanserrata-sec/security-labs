#!/usr/bin/env python3
"""Reubica la base «Laboratorios» al final de la página y archiva la que quedó arriba.

Notion no permite mover bloques por API: se crea la base otra vez dentro de la
página (queda al final, después del texto), se copian las filas y se archiva la vieja.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
PAGINA = "2b75a16a-365b-81b4-8440-cb557e405c5c"
VIEJA = "3562ed01-40ba-4ccb-8fd1-88e72944a98e"
VIEJA_FUENTE = "b3d5fbb3-3745-4d83-83de-791372ea3b77"


def clave() -> str:
    for linea in Path(os.path.expanduser("~/.hermes/.env")).read_text().splitlines():
        if linea.startswith("NOTION_API_KEY="):
            return linea.split("=", 1)[1].strip()
    raise SystemExit("sin NOTION_API_KEY")


def llamar(metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
    datos = json.dumps(cuerpo).encode() if cuerpo else None
    req = urllib.request.Request(
        f"{API}{ruta}",
        data=datos,
        method=metodo,
        headers={
            "Authorization": f"Bearer {clave()}",
            "Notion-Version": VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{metodo} {ruta} -> {e.code}: {e.read().decode()[:300]}")


ESQUEMA = {
    "Nombre": {"title": {}},
    "Plataforma": {"select": {"options": [{"name": "VulnHub"}, {"name": "Empresa"}, {"name": "TryHackMe"}]}},
    "Dificultad": {"select": {"options": [{"name": "principiante"}, {"name": "media"}, {"name": "alta"}]}},
    "Sistema": {"rich_text": {}},
    "Técnicas": {"rich_text": {}},
    "Writeup": {"url": {}},
    "Estado": {"select": {"options": [{"name": "publicado"}, {"name": "en revisión"}]}},
    "Fecha": {"date": {}},
}


def main() -> None:
    filas = llamar("POST", f"/data_sources/{VIEJA_FUENTE}/query", {"page_size": 50}).get("results", [])
    print("filas en la base vieja:", len(filas))

    nueva = llamar(
        "POST",
        "/databases",
        {
            "parent": {"type": "page_id", "page_id": PAGINA},
            "title": [{"type": "text", "text": {"content": "Laboratorios"}}],
            "initial_data_source": {"properties": ESQUEMA},
        },
    )
    fuente = (nueva.get("data_sources") or [{}])[0].get("id")
    print("base nueva:", nueva["id"], "| data source:", fuente)

    for fila in filas:
        props = {}
        for nombre, valor in fila["properties"].items():
            tipo = valor["type"]
            if tipo == "title":
                props[nombre] = {"title": valor["title"]}
            elif tipo == "rich_text":
                props[nombre] = {"rich_text": valor["rich_text"]}
            elif tipo == "select" and valor["select"]:
                props[nombre] = {"select": {"name": valor["select"]["name"]}}
            elif tipo == "url" and valor["url"]:
                props[nombre] = {"url": valor["url"]}
            elif tipo == "date" and valor["date"]:
                props[nombre] = {"date": {"start": valor["date"]["start"]}}
        llamar("POST", "/pages", {"parent": {"data_source_id": fuente}, "properties": props})
    print("filas copiadas:", len(filas))

    llamar("PATCH", f"/databases/{VIEJA}", {"in_trash": True})
    print("base vieja archivada:", VIEJA)


if __name__ == "__main__":
    main()
