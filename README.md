# Labs y SOC

Documentación de laboratorios de pentesting y de proyectos de detección y SOC.
Todo el contenido se ha ejecutado en **entornos propios de práctica** (VulnHub y laboratorio
local). No hay datos de clientes. En los writeups sí aparecen la IP y las credenciales de la
máquina del reto: son laboratorios públicos y retirados, y sin ellas el writeup no sirve.

## Por qué existe

Escribo cada laboratorio una vez y de ahí salen tres cosas: el histórico de git, esta web y las
piezas de contenido. Documentar es el principio de la cadena, no el final.

## Labs y proyectos

<div class="cards">
  <a class="card" href="labs/basic2/">
    <span class="tag">Lab · VulnHub</span>
    <h3>Basic Pentesting 2</h3>
    <p>Un directorio de desarrollo publica las notas del equipo y SMB acepta conexiones anónimas:
    dos usuarios, una clave privada legible y root por diccionario.</p>
    <span class="meta">Ubuntu 16.04 · principiante · mi primer lab <span class="go">→</span></span>
  </a>
  <a class="card" href="labs/darkhole2/">
    <span class="tag">Lab · VulnHub</span>
    <h3>DarkHole 2</h3>
    <p>Del repositorio <code>.git</code> expuesto a root: credenciales en el historial, inyección SQL,
    reverse shell y <code>sudo</code> sobre Python.</p>
    <span class="meta">Ubuntu 20.04 · dificultad media · 10 pasos <span class="go">→</span></span>
  </a>
  <a class="card" href="labs/lupin/">
    <span class="tag">Lab · LupinOne</span>
    <h3>LupinOne</h3>
    <p>Una clave privada publicada «para que no la encuentren», una passphrase de diccionario y dos
    saltos de usuario por permisos: módulo del sistema escribible y <code>pip</code> con sudo.</p>
    <span class="meta">Debian 11 · dificultad media · tres usuarios <span class="go">→</span></span>
  </a>
  <a class="card" href="soc/wazuh-n8n-thehive/">
    <span class="tag">SOC · Detección</span>
    <h3>Wazuh → n8n → TheHive</h3>
    <p>Flujo de alerta completo: validación, enriquecimiento, deduplicación y apertura de caso, con
    reglas probadas y playbook de triaje.</p>
    <span class="meta">Arquitectura · reglas · runbook <span class="go">→</span></span>
  </a>
  <a class="card" href="plantillas/writeup.html">
    <span class="tag">Plantillas</span>
    <h3>Writeup, informe y runbook</h3>
    <p>Tres esqueletos listos: writeup de laboratorio, informe de pentest con CVSS y CWE, y runbook
    de triaje para el SOC.</p>
    <span class="meta">Reutilizables · en Markdown <span class="go">→</span></span>
  </a>
</div>

## Estructura

```
labs/<maquina>/        writeup, evidencia y scripts
soc/<proyecto>/        arquitectura, reglas y playbooks
plantillas/            writeup, informe de pentest, runbook de SOC
herramientas/          saneador de secretos
public/                lo que se publica en GitHub Pages
```

## Reglas del repositorio

1. **Datos de cliente, nunca.** En `labs/` sí aparecen la IP, el hash y las credenciales **del reto**:
   son máquinas públicas y retiradas, y sin ellas el writeup no sirve.
2. El saneador (`herramientas/sanear.py`) corre en cada push: bloquea **tokens, claves privadas y
   cabeceras** en cualquier ruta, y credenciales o IPs fuera de `labs/`.
3. Cada lab lleva su apartado de **detección**: qué alerta lo habría cazado y con qué técnica.

## Uso

```bash
python3 herramientas/sanear.py --check .   # busca secretos
python3 herramientas/sanear.py --fix .     # los sustituye por marcadores
```

## Licencia

Código y scripts: MIT. Textos y writeups: CC BY-NC-SA 4.0.

> Todo el material es educativo y de laboratorio propio. No se publica ninguna técnica contra
> sistemas de terceros ni datos que no sean míos.
