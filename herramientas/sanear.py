#!/usr/bin/env python3
"""Saneador de secretos para un repositorio público.

Uso:
    python3 herramientas/sanear.py --check .    # falla (exit 1) si hay algo sensible
    python3 herramientas/sanear.py --fix .      # sustituye por marcadores

Reglas:
  · En `labs/` se permiten la IP, el correo, el hash y las credenciales **del reto**:
    son laboratorios públicos y retirados, y sin ellos el writeup no sirve.
  · En cualquier ruta se bloquean los secretos reales: tokens de servicio, claves
    privadas y cabeceras de autorización. Un lab nunca necesita eso.
  · Fuera de `labs/` se aplica la regla estricta: ni IPs ni credenciales.
Las excepciones puntuales van en .sanear-allow (una regex por línea).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENSIONES = {".md", ".txt", ".py", ".sh", ".yml", ".yaml", ".json", ".conf", ".ini", ".env.example", ".html", ".csv"}
IGNORAR_DIRS = {".git", "__pycache__", ".venv", "node_modules", "public/evidencia"}

# Nunca, en ninguna ruta: esto no pertenece a un laboratorio público.
PATRONES_SIEMPRE = [
    ("token de API", re.compile(r"\b(sk|ghp|gho|ghs|AKIA|xoxb|shpat)[-_][A-Za-z0-9_-]{12,}\b"), "<TOKEN>"),
    ("clave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "<CLAVE-PRIVADA>"),
    ("cabecera bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}"), "Bearer <TOKEN>"),
]

# Solo fuera de labs/: el reto puede llevarlas a la vista.
PATRONES_FUERA_DE_LABS = [
    ("IP privada/publica", re.compile(r"\b(?!127\.0\.0\.1|0\.0\.0\.0)(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
    ("correo", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"), "<CORREO>"),
    ("credencial en URL", re.compile(r"://[^/\s:@]+:[^/\s@]+@"), "://<CREDENCIAL>@"),
    ("hash de contraseña", re.compile(r"\$(2[aby]|1|6)\$[./A-Za-z0-9$]{8,}"), "<HASH>"),
    ("asignacion de secreto", re.compile(r"(?i)\b(pass(word)?|passwd|pwd|secret|api[_-]?key|token)\b\s*[:=]\s*['\"]?[^\s'\"<]{2,}"), r"\1: <REDACTADO>"),
    ("contrasena en comando", re.compile(r"(?i)(mysql|mysqldump|sshpass|curl|psql)[^\n]{0,40}-p\s*['\"]?[^\s'\"]{3,}"), r"\1 -p <REDACTADO>"),
]


def cargar_excepciones(raiz: Path) -> list[re.Pattern]:
    f = raiz / ".sanear-allow"
    if not f.exists():
        return []
    salida = []
    for linea in f.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            salida.append(re.compile(linea))
    return salida


def ficheros(raiz: Path):
    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        if any(parte in IGNORAR_DIRS for parte in p.parts):
            continue
        if p.name in {"LICENSE", ".sanear-allow", "sanear.py"} or p.suffix.lower() not in EXTENSIONES:
            continue
        yield p


def es_lab(relativa: Path) -> bool:
    """Un writeup de laboratorio: puede mostrar credenciales del reto."""
    return relativa.parts[:1] == ("labs",)


def procesar(raiz: Path, arreglar: bool) -> int:
    excepciones = cargar_excepciones(raiz)
    hallazgos = 0
    for f in ficheros(raiz):
        try:
            texto = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relativa = f.relative_to(raiz)
        patrones = PATRONES_SIEMPRE if es_lab(relativa) else PATRONES_SIEMPRE + PATRONES_FUERA_DE_LABS
        original = texto
        for i, linea in enumerate(texto.splitlines(), start=1):
            if any(ex.search(linea) for ex in excepciones):
                continue
            for nombre, patron, _ in patrones:
                m = patron.search(linea)
                if not m:
                    continue
                hallazgos += 1
                muestra = m.group(0)
                if len(muestra) > 60:
                    muestra = muestra[:57] + "..."
                print(f"{relativa}:{i}: {nombre}: {muestra}")
        if arreglar and texto != original:
            for _, patron, reemplazo in patrones:
                texto = patron.sub(reemplazo, texto)
            f.write_text(texto, encoding="utf-8")
    return hallazgos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ruta", nargs="?", default=".")
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--check", action="store_true", help="solo comprobar (exit 1 si hay hallazgos)")
    grupo.add_argument("--fix", action="store_true", help="sustituir por marcadores")
    args = ap.parse_args()

    raiz = Path(args.ruta).resolve()
    n = procesar(raiz, arreglar=args.fix)
    if n:
        print(f"\n{n} hallazgo(s)." + ("" if args.fix else " Ejecuta --fix o edita a mano."))
        return 0 if args.fix else 1
    print("Sin hallazgos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
