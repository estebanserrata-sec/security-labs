#!/usr/bin/env python3
"""Crea en Notion la base de datos de laboratorios y la rellena desde el repositorio."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
REPO = Path("/home/hermes/security-labs")
SITIO = "https://estebanserrata-sec.github.io/security-labs/labs"


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
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{metodo} {ruta} -> {e.code}: {e.read().decode()[:400]}")


def labs() -> list[dict]:
    salida = []
    for readme in sorted(REPO.glob("labs/*/README.md")):
        texto = readme.read_text(encoding="utf-8")
        slug = readme.parent.name

        def campo(nombre: str) -> str:
            m = re.search(rf"\|\s*\*\*{nombre}\*\*\s*\|\s*([^|]+)\|", texto)
            return m.group(1).strip() if m else ""

        titulo = texto.splitlines()[0].lstrip("# ").strip()
        plataforma = campo("Plataforma")
        sistema = campo("Sistema")
        dificultad = campo("Dificultad")
        fecha = campo("Fecha")
        tecnicas = ""
        m = re.search(r"\*\*Técnicas:\*\*\s*(.+)", texto)
        if m:
            tecnicas = m.group(1).strip()
        salida.append(
            {
                "titulo": titulo,
                "slug": slug,
                "plataforma": plataforma,
                "sistema": sistema,
                "dificultad": dificultad,
                "fecha": fecha,
                "tecnicas": tecnicas,
                "url": f"{SITIO}/{slug}/",
            }
        )
    return salida


def main() -> None:
    # 1. la base de datos, dentro de la página del sitio personal
    busqueda = llamar("POST", "/search", {"query": "Sitio web personal", "page_size": 5})
    pagina = next(
        (r for r in busqueda.get("results", []) if r["object"] == "page" and "Sitio web" in json.dumps(r)),
        None,
    )
    if not pagina:
        raise SystemExit("no encuentro la página «Sitio web personal»")

    db = llamar(
        "POST",
        "/databases",
        {
            "parent": {"type": "page_id", "page_id": pagina["id"]},
            "title": [{"type": "text", "text": {"content": "Laboratorios"}}],
            "initial_data_source": {"properties": {
                    "Nombre": {"title": {}},
                    "Plataforma": {"select": {"options": [{"name": "VulnHub"}, {"name": "Empresa"}, {"name": "TryHackMe"}]}},
                    "Dificultad": {"select": {"options": [{"name": "principiante"}, {"name": "media"}, {"name": "alta"}]}},
                    "Sistema": {"rich_text": {}},
                    "Técnicas": {"rich_text": {}},
                    "Writeup": {"url": {}},
                    "Estado": {"select": {"options": [{"name": "publicado"}, {"name": "en revisión"}]}},
                    "Fecha": {"date": {}},
                },
            },
        },
    )
    fuente = (db.get("data_sources") or [{}])[0].get("id")
    print("base de datos:", db.get("id"), "| data source:", fuente)

    # archiva la base vacía creada en el intento anterior
    try:
        llamar("PATCH", "/databases/b09c3ce9-6ac1-478d-86bc-2fee2d65858b", {"archived": True})
        print("base vacía anterior archivada")
    except SystemExit as e:
        print("no se pudo archivar la anterior:", e)

    # 2. una fila por laboratorio
    for lab in labs():
        props = {
            "Nombre": {"title": [{"text": {"content": lab["titulo"]}}]},
            "Sistema": {"rich_text": [{"text": {"content": lab["sistema"]}}]},
            "Técnicas": {"rich_text": [{"text": {"content": lab["tecnicas"][:1900]}}]},
            "Writeup": {"url": lab["url"]},
            "Estado": {"select": {"name": "publicado"}},
        }
        if lab["plataforma"]:
            props["Plataforma"] = {"select": {"name": "Empresa" if "Empresa" in lab["plataforma"] else "VulnHub"}}
        if lab["dificultad"]:
            props["Dificultad"] = {"select": {"name": lab["dificultad"].lower()}}
        if re.match(r"\d{4}-\d{2}-\d{2}", lab["fecha"]):
            props["Fecha"] = {"date": {"start": lab["fecha"]}}
        fila = llamar(
            "POST",
            "/pages",
            {"parent": {"data_source_id": fuente} if fuente else {"database_id": db["id"]}, "properties": props},
        )
        print(f"  {lab['titulo']:<24} -> {fila['id']}")


if __name__ == "__main__":
    main()
