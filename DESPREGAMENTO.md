# Despregamento de AgroXest360

Instrucións para instalar a aplicación nun servidor e mantela en funcionamento.

## Requisitos

- Calquera sistema onde funcione Python 3.11 ou posterior. Para servidores recoméndase Linux (Debian, Ubuntu, Fedora, Rocky/AlmaLinux, openSUSE, Arch…), pero a aplicación tamén funciona en macOS e Windows.
- [uv](https://docs.astral.sh/uv/) ou, se non, `pip` (ver o paso 1).
- A biblioteca Pango, que usa WeasyPrint para xerar os PDF:

  | Sistema | Orde |
  |---|---|
  | Debian, Ubuntu | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0` |
  | Fedora, Rocky, AlmaLinux, RHEL | `sudo dnf install pango` |
  | openSUSE | `sudo zypper install pango` |
  | Arch | `sudo pacman -S pango` |
  | Alpine | `sudo apk add pango` |
  | macOS | `brew install pango` |
  | Windows | Instalar Pango con [MSYS2](https://www.msys2.org/) (`pacman -S mingw-w64-x86_64-pango`), como indica a documentación de WeasyPrint |

- Un dominio e un proxy inverso con HTTPS: Caddy, nginx ou Apache, por exemplo.

Os exemplos de usuario do sistema e de servizo (pasos 1 e 5) son para Linux con systemd. Noutros sistemas úsase o seu equivalente: un servizo de Windows, `launchd` en macOS ou outro xestor de procesos.

## 1. Instalación

```bash
sudo useradd --system --create-home --home-dir /srv/agroxest360 agroxest360
sudo -u agroxest360 -i
git clone https://github.com/xabierseixo/horta.git app
cd app
uv sync --no-dev
```

`uv sync` instala todas as dependencias de Python coas versións exactas fixadas en `uv.lock`. As principais son:

| Paquete | Para que |
|---|---|
| nicegui | Interface web |
| sqlalchemy e alembic | Base de datos e migracións |
| pydantic | Validación de datos |
| bcrypt | Cifrado dos contrasinais |
| httpx | Conexión con servizos externos (MeteoGalicia, MAPA, XEAGA) |
| openpyxl, weasyprint e odfpy | Informes en Excel, PDF e ODS |
| shapely | Xeometría das parcelas |
| segno | Códigos QR dos lotes |
| loguru | Rexistro de erros |
| python-dateutil | Cálculo de datas |

Sen uv, pódense instalar con pip nun contorno virtual (Python 3.11 ou posterior):

```bash
python3 -m venv .venv
.venv/bin/pip install .
```

Neste caso, nos pasos seguintes substitúese `uv run` por `.venv/bin/` (por exemplo, `.venv/bin/alembic upgrade head` e `.venv/bin/horta`).

## 2. Configuración

A configuración faise con variables de contorno. Gárdanse nun ficheiro, por exemplo `/srv/agroxest360/entorno`, con permisos `600`:

```bash
HORTA_DATABASE_URL=sqlite:////srv/agroxest360/datos/horta.db
HORTA_STORAGE_SECRET=<cadea aleatoria longa>
HORTA_COPIAS_DIR=/srv/agroxest360/datos/copias
HORTA_DOCUMENTOS_DIR=/srv/agroxest360/datos/documentos
HORTA_FOTOS_DIR=/srv/agroxest360/datos/fotos
HORTA_TESELAS_DIR=/srv/agroxest360/datos/teselas
```

| Variable | Función | Valor por defecto |
|---|---|---|
| `HORTA_DATABASE_URL` | Base de datos | `sqlite:///horta.db` no cartafol da app |
| `HORTA_STORAGE_SECRET` | Segredo que asina as sesións | Créase ao chou en `~/.local/share/horta/segredo-sesion` |
| `HORTA_COPIAS_DIR` | Copias de seguridade diarias | `~/.local/share/horta/copias` |
| `HORTA_DOCUMENTOS_DIR` | Documentos e certificados | `~/.local/share/horta/documentos` |
| `HORTA_FOTOS_DIR` | Fotografías | `~/.local/share/horta/fotos` |
| `HORTA_TESELAS_DIR` | Caché dos mapas | `~/.local/share/horta/teselas` |
| `HORTA_COPIAS` | `0` desactiva as copias diarias | activadas |
| `HORTA_ACTUALIZAR` | `0` desactiva a descarga automática dos catálogos e do rexistro de fitosanitarios | activada |
| `HORTA_CODIGO_FONTE` | Enderezo do código fonte que se mostra no aviso legal (obriga da licenza AGPL) | `https://github.com/xabierseixo/horta` |
| `HORTA_XEAGA_URL`, `HORTA_XEAGA_APP` | Conexión co caderno dixital da Xunta (XEAGA) | sen conexión |

O segredo pódese xerar con:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 3. Base de datos

```bash
mkdir -p /srv/agroxest360/datos
set -a; . /srv/agroxest360/entorno; set +a
uv run alembic upgrade head
```

## 4. Primeiro usuario administrador

Créase unha soa vez. Cambia o correo e o contrasinal antes de executalo:

```bash
set -a; . /srv/agroxest360/entorno; set +a
uv run python -c "
from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
with get_session() as session:
    session.add(Usuario(nome='Admin', email='admin@example.com',
                        password_hash=hash_password('cambiar-isto'),
                        rol=RolGlobal.ADMIN, activo=True))
    session.commit()
"
```

Os demais usuarios créanse desde a propia aplicación.

## 4 bis. Datos legais

Antes de abrir o servizo a outras persoas, o administrador ten que completar en **Administración → Datos legais** os datos do responsable do tratamento: titular, NIF, enderezo e correo de contacto. Opcionalmente, pode engadir o delegado de protección de datos e onde se gardan os datos. Con eles complétanse o aviso legal e a política de privacidade (`/legal/aviso` e `/legal/privacidade`), que cada persoa usuaria ten que aceptar ao entrar por primeira vez.

Os textos son unha base e convén que os revise un asesor antes de usalos.

## 5. Servizo do sistema

`/etc/systemd/system/agroxest360.service`:

```ini
[Unit]
Description=AgroXest360
After=network.target

[Service]
User=agroxest360
WorkingDirectory=/srv/agroxest360/app
EnvironmentFile=/srv/agroxest360/entorno
ExecStart=/srv/agroxest360/.local/bin/uv run horta
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agroxest360
```

A aplicación escoita no porto 8081.

## 6. Proxy inverso con HTTPS

A aplicación escoita no porto 8081 en todas as interfaces do servidor. O proxy inverso dálle o dominio e o HTTPS, e ten que permitir WebSocket, porque a interface depende del. Convén pechar o porto 8081 no cortalumes (por exemplo, `ufw deny 8081` ou `firewall-cmd --remove-port=8081/tcp`), para que só se poida entrar a través do proxy.

### Caddy

`/etc/caddy/Caddyfile` (obtén o certificado automaticamente):

```
agroxest360.exemplo.gal {
    reverse_proxy 127.0.0.1:8081
}
```

### nginx

```nginx
server {
    listen 443 ssl;
    server_name agroxest360.exemplo.gal;
    ssl_certificate     /etc/letsencrypt/live/agroxest360.exemplo.gal/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agroxest360.exemplo.gal/privkey.pem;
    client_max_body_size 25m;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 1h;
    }
}
```

### Apache (2.4.47 ou posterior)

Activar os módulos: `a2enmod proxy proxy_http proxy_wstunnel headers ssl` (en Debian/Ubuntu; noutros sistemas, cargalos en `httpd.conf`).

```apache
<VirtualHost *:443>
    ServerName agroxest360.exemplo.gal
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/agroxest360.exemplo.gal/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/agroxest360.exemplo.gal/privkey.pem
    LimitRequestBody 26214400

    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    ProxyPass        / http://127.0.0.1:8081/ upgrade=websocket timeout=3600
    ProxyPassReverse / http://127.0.0.1:8081/
</VirtualHost>
```

Nas versións de Apache anteriores á 2.4.47, o WebSocket configúrase con `mod_rewrite`, redirixindo as peticións con `Upgrade: websocket` a `ws://127.0.0.1:8081/`.

O límite de 25 MB do tamaño das peticións permite subir documentos de ata 20 MB.

## 7. Catálogos oficiais

Na primeira instalación, a aplicación descarga en segundo plano os catálogos e o rexistro de produtos fitosanitarios do MAPA. Despois mantenos actualizados.

Os catálogos do FEGA (SIEX) descárganse no navegador e impórtanse con:

```bash
uv run horta-catalogos importar <cartafol>
uv run horta-catalogos nomes-galegos
```

O estado dos catálogos vese no panel de administración.

## 8. Copias de seguridade

A aplicación fai cada día unha copia da base de datos en `HORTA_COPIAS_DIR`. Os administradores poden descargala desde o panel de administración. Convén levar as copias e o cartafol de fotos a outro equipo de forma periódica, por exemplo con `rsync` ou cunha copia ao almacenamento externo.

## 9. Actualización

```bash
sudo -u agroxest360 -i
cd app
git pull
uv sync --no-dev
set -a; . /srv/agroxest360/entorno; set +a
uv run alembic upgrade head
exit
sudo systemctl restart agroxest360
```

## 10. Rexistros

A aplicación escribe o seu rexistro en `logs/horta.log`, dentro do cartafol da app. Os erros do servizo vense con:

```bash
journalctl -u agroxest360 -f
```
