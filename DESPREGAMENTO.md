# Despregamento de AgroXest360

Instrucións para instalar a aplicación nun servidor e mantela en funcionamento.

## Requisitos

- Servidor Linux (Debian 12, Ubuntu 22.04 ou posterior).
- Python 3.11 e [uv](https://docs.astral.sh/uv/).
- Bibliotecas do sistema para xerar PDF (WeasyPrint):
  ```bash
  sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
  ```
- Un dominio e un proxy inverso con HTTPS (por exemplo, Caddy ou nginx).

## 1. Instalación

```bash
sudo useradd --system --create-home --home-dir /srv/agroxest360 agroxest360
sudo -u agroxest360 -i
git clone https://github.com/xabierseixo/horta.git app
cd app
uv sync --no-dev
```

## 2. Configuración

A configuración faise con variables de contorno. Gárdanse nun ficheiro, por exemplo `/srv/agroxest360/entorno`, con permisos `600`:

```bash
HORTA_DATABASE_URL=sqlite:////srv/agroxest360/datos/horta.db
HORTA_STORAGE_SECRET=<cadea aleatoria longa>
HORTA_COPIAS_DIR=/srv/agroxest360/datos/copias
HORTA_FOTOS_DIR=/srv/agroxest360/datos/fotos
HORTA_TESELAS_DIR=/srv/agroxest360/datos/teselas
```

| Variable | Función | Valor por defecto |
|---|---|---|
| `HORTA_DATABASE_URL` | Base de datos | `sqlite:///horta.db` no cartafol da app |
| `HORTA_STORAGE_SECRET` | Segredo que asina as sesións | Créase ao chou en `~/.local/share/horta/segredo-sesion` |
| `HORTA_COPIAS_DIR` | Copias de seguridade diarias | `~/.local/share/horta/copias` |
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

Exemplo con Caddy (`/etc/caddy/Caddyfile`), que obtén o certificado automaticamente:

```
agroxest360.exemplo.gal {
    reverse_proxy 127.0.0.1:8081
}
```

Se se usa nginx, o proxy ten que permitir WebSocket (cabeceiras `Upgrade` e `Connection`), porque a interface depende del.

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
