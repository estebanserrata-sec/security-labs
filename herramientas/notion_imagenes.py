#!/usr/bin/env python3
"""Genera la portada y el icono de la página de Notion, en la paleta del sitio."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (8, 10, 13)
BG2 = (14, 18, 22)
AMBER = (242, 180, 65)
INK = (239, 245, 248)
MUTED = (138, 154, 166)
LINE = (31, 40, 48)

INTER = "/home/hermes/.fonts/Inter-variable.ttf"
MONO = "/home/hermes/.fonts/JetBrainsMono-variable.ttf"
SALIDA = Path("/home/hermes/security-labs/assets/img")


def fuente(ruta: str, tam: int, peso: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(ruta, tam)
    try:
        f.set_variation_by_axes([peso]) if peso else None
    except Exception:
        pass
    return f


def rejilla(d: ImageDraw.ImageDraw, w: int, h: int, paso: int = 64) -> None:
    for x in range(0, w, paso):
        d.line([(x, 0), (x, h)], fill=LINE, width=1)
    for y in range(0, h, paso):
        d.line([(0, y), (w, y)], fill=LINE, width=1)


def portada() -> None:
    w, h = 1500, 500
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)

    # degradado suave de arriba a abajo
    for y in range(h):
        t = y / h
        c = tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)

    rejilla(d, w, h)
    d.rectangle([0, 0, 14, h], fill=AMBER)

    d.text((86, 96), "ESTEBAN SERRATA", font=fuente(INTER, 92, 700), fill=INK)
    d.text((88, 214), "SYSTEM ENGINEER · CYBERSECURITY SPECIALIST", font=fuente(MONO, 26), fill=AMBER)
    d.text((88, 262), "Pentesting · Automatización de seguridad · SOC · Hardening de red", font=fuente(MONO, 24), fill=MUTED)

    # marcador de sección
    d.rectangle([88, 332, 108, 352], fill=AMBER)
    d.text((124, 330), "SOC ANALYST · 6+ AÑOS EN DETECCIÓN", font=fuente(MONO, 22), fill=MUTED)

    # monograma a la derecha
    d.rectangle([1178, 150, 1408, 380], outline=LINE, width=2)
    d.text((1216, 214), "ES", font=fuente(INTER, 108, 700), fill=AMBER)

    img.save(SALIDA / "notion-portada.png", optimize=True)
    print("portada:", (SALIDA / "notion-portada.png").stat().st_size, "bytes")


def icono() -> None:
    s = 280
    img = Image.new("RGB", (s, s), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, s, s], outline=LINE, width=2)
    d.rectangle([0, 0, 10, s], fill=AMBER)
    d.text((74, 72), "ES", font=fuente(INTER, 118, 700), fill=INK)
    d.text((78, 200), "SEC", font=fuente(MONO, 30), fill=AMBER)
    img.save(SALIDA / "notion-icono.png", optimize=True)
    print("icono:", (SALIDA / "notion-icono.png").stat().st_size, "bytes")


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    portada()
    icono()
