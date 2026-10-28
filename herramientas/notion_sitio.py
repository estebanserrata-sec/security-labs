#!/usr/bin/env python3
"""Rehace la página «Sitio web personal» de Notion con proyectos reales del repositorio.

Borra el contenido de plantilla (conserva las bases de datos enlazadas) y escribe
un portfolio verificable: laboratorios, SOC, automatización y contacto.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
PAGINA = "2b75a16a-365b-81b4-8440-cb557e405c5c"

PORTFOLIO = """# Esteban Serrata
**System engineer · Cybersecurity Specialist**
Pentesting, automatización de seguridad, SOC y hardening de red
Santo Domingo Este, República Dominicana

<callout icon="🔐" color="blue_bg">
	Ingeniero de Sistemas y especialista en ciberseguridad con más de **6 años y medio en operaciones de SOC** y una base de **8 años en soporte de infraestructura tecnológica**. Certificado como **SOC Analyst (CSA)** e **ISC2 Certified in Cybersecurity (CC)**. Documento lo que hago con evidencia de cada paso.
</callout>

## Sobre mí

Mi perfil se centra en fortalecer la postura de seguridad de la infraestructura corporativa, desde el monitoreo fino hasta la mitigación activa.

- **Operaciones SOC y detección**: gestión e implementación de plataformas SIEM (Wazuh, NetWitness), correlación de eventos, telemetría de endpoints con Sysmon y desarrollo de reglas personalizadas para detección precisa y menos falsos positivos.
- **Orquestación y automatización (SOAR)**: flujos de trabajo que conectan el monitoreo con la gestión de incidentes (TheHive) para reducir el tiempo medio de respuesta.
- **Seguridad ofensiva y hardening**: pentesting, evaluación de vulnerabilidades y controles de seguridad en servidores Linux/Proxmox y redes.
- **Base de ingeniería**: arquitectura de redes, virtualización y sistemas, para entender el impacto real de cada incidente en la continuidad del negocio.

## Experiencia

### SOC Analyst · Confidencial
**noviembre 2019 — actualidad** · Santo Domingo, Distrito Nacional, República Dominicana

Operación de SOC en jornada completa durante más de seis años: monitoreo, triaje y respuesta a incidentes, con automatización de los flujos repetitivos.

## Proyectos reales

### Laboratorios documentados

- **LupinOne** · Empresa · media · 2026 — de `netdiscover` a root pasando por dos usuarios, sin un solo exploit: directorio `/~secret/` encontrado con ffuf, fichero oculto en Base 58, clave privada publicada, módulo del sistema en 777 y `pip` con sudo.
- **DarkHole 2** · VulnHub · media · 2026 — repositorio `.git` expuesto, credenciales en el historial, inyección en el parámetro `id`, reverse shell y escalada con Python autorizado por sudo.
- **Basic Pentesting 2** · VulnHub · principiante — SMB anónimo, notas del equipo en un directorio de desarrollo, clave privada cifrada y escalada por contraseña reutilizada.

<mention-page url="https://estebanserrata-sec.github.io/security-labs/labs/">Writeups publicados</mention-page>

### SOC y detección

Flujo completo en producción propia: **Wazuh → n8n → TheHive**. La alerta se valida, se enriquece, se deduplica y abre caso, con playbook de triaje y reglas propias probadas con `wazuh-logtest` —incluido el diagnóstico de seis reglas que no disparaban por colgar de un `if_sid` equivocado.

### Automatización y contenido

Pipeline que convierte un JSON en carrusel y en reel vertical con narración y efectos: **Remotion** para la animación, **ffmpeg** para el montaje, **Piper** para la voz y **GitHub Pages** como destino. Un solo origen de contenido, tres salidas.

## Certificaciones y formación

**Certificaciones**

- **Certified SOC Analyst (CSA)** — EC-Council · junio 2024
- **Certified in Cybersecurity (CC)** — ISC2 · mayo 2024
- **Ethical Hacker** — Cisco Networking Academy · junio 2025
- **Linux Essentials LPI** — Cisco Networking Academy · mayo 2024
- **SIEM · Seguridad gestionada** — Cyberacademy Capabilita · septiembre 2021

**Formación académica**

- **Ingeniero de Sistemas** — Universidad Dominico Americano

## Habilidades

- **SIEM y detección**: Wazuh, NetWitness, Sysmon, MITRE ATT&CK, reglas y decoders, triaje.
- **SOAR y automatización**: n8n, TheHive, Python, Bash, APIs (GitHub, Notion).
- **Ofensiva**: nmap, ffuf, Burp Suite, sqlmap, hydra, john, linPEAS, git-dumper.
- **Infraestructura**: Linux, Proxmox, virtualización, segmentación de red, hardening.
- **Contenido técnico**: ffmpeg, Remotion, diseño de carruseles, narración sintética.

## Contacto

- **Web y writeups**: https://estebanserrata-sec.github.io/security-labs/
- **GitHub**: https://github.com/estebanserrata-sec
- **LinkedIn**: https://www.linkedin.com/in/estebanserrata
- **Instagram**: https://www.instagram.com/estebanserrata.sec

> La seguridad no es un producto: es un proceso que se documenta.
"""


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


def hijos(pagina: str) -> list[dict]:
    salida, cursor = [], None
    while True:
        ruta = f"/blocks/{pagina}/children?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        d = llamar("GET", ruta)
        salida += d.get("results", [])
        if not d.get("has_more"):
            return salida
        cursor = d.get("next_cursor")


def main() -> None:
    bloques = hijos(PAGINA)
    print("bloques actuales:", len(bloques))

    borrados = conservados = 0
    for b in bloques:
        if b["type"] == "child_database":
            conservados += 1
            continue
        llamar("PATCH", f"/blocks/{b['id']}", {"archived": True})
        borrados += 1
    print(f"borrados: {borrados} · bases de datos conservadas: {conservados}")

    llamar("PATCH", f"/pages/{PAGINA}/markdown", {"type": "insert_content", "insert_content": {"content": PORTFOLIO}})
    print("contenido nuevo escrito")

    # verificación: leer la página otra vez
    md = llamar("GET", f"/pages/{PAGINA}/markdown").get("markdown", "")
    for esperado in ("Esteban Serrata", "LupinOne", "DarkHole 2", "Basic Pentesting 2", "Wazuh", "estebanserrata-sec"):
        print(("✓" if esperado in md else "✗"), esperado)
    print("sin restos de plantilla:", all(x not in md for x in ("SecureNet", "CyberGuard", "CISSP", "Reducción del 45%")))


if __name__ == "__main__":
    main()

# Nota de uso: el script archiva todos los bloques de texto de la página
# (conserva las bases de datos enlazadas) y vuelve a escribir el portfolio,
# así que se puede relanzar cuando cambie el contenido.
