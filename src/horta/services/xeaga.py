"""Cliente do Interface Único Común (IUWS) do CUE da Xunta (XEAGA): FEGA, Anexo VI v4.10
.

Entrada como «productor particular»: o titular identifícase na Xunta e o token volve a horta
pola URL de volta rexistrada. horta non garda o token no disco nin ve as claves do titular.
As probas usan exemplos gardados: nunca a rede."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Cabeceira obrigatoria desde a versión 5.9 do interface (Anexo VI 4.10, Anexo 6)
IUWS_CONSUMER = "SGA/IUWS"
# Tamaño máximo dun envío (Anexo VI §3.1)
MAX_BYTES = 2 * 1024 * 1024
# comprobarEstado: «pendente de procesamento» (Anexo VI §3.6)
CODIGO_PENDENTE = 3
# Mensaxes por actividade que din que xa non se pode cambiar alí (Anexo 1)
CODIGOS_PECHADA = {14, 17, 18}


class XeagaErro(Exception):
    """A Xunta non respondeu ou rexeitou a petición."""


@dataclass
class Token:
    valor: str
    nif: str | None
    caduca: datetime | None

    def valido(self, agora: datetime | None = None) -> bool:
        agora = agora or datetime.now(timezone.utc)
        return self.caduca is None or agora < self.caduca


def ler_token(valor: str) -> Token:
    """Le o NIF (cif) e a caducidade (exp) do JWT. Non comproba a sinatura: iso faino a
    Xunta en cada chamada; horta só o usa para non mesturar titulares e saber cando caduca."""
    try:
        carga = valor.split(".")[1]
        datos = json.loads(base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)))
    except (IndexError, ValueError) as e:
        raise XeagaErro("O token da Xunta non ten o formato esperado") from e
    exp = datos.get("exp")
    return Token(valor, datos.get("cif"),
                 datetime.fromtimestamp(exp, timezone.utc) if exp else None)


@dataclass
class Mensaxe:
    codigo: int | None
    texto: str


@dataclass
class Resultado:
    codigo: str  # OK, PARCIAL, FALLO, ERROR…
    mensaxes: list[Mensaxe]
    cuaderno: list[dict[str, Any]] | None = None
    rea: list[dict[str, Any]] | None = None

    @property
    def pendente(self) -> bool:
        return self.cuaderno is None and any(m.codigo == CODIGO_PENDENTE
                                             for m in self.mensaxes)


def _num(valor: Any) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def ler_resultado(resposta: dict[str, Any]) -> Resultado:
    """A resposta do IUWS. Os exemplos oficiais traen os datos dentro de «resultado» ou fóra;
    o detalle chámase detalleImportacion ou detalleOperacion e pode ser lista ou un só."""
    corpo = resposta.get("resultado", resposta)
    detalle = corpo.get("detalleImportacion", corpo.get("detalleOperacion")) or []
    if isinstance(detalle, dict):
        detalle = [detalle]
    mensaxes = [Mensaxe(_num(d.get("codigo")), str(d.get("descripcion", ""))) for d in detalle]

    def bloque(nome: str) -> list[dict[str, Any]] | None:
        valor = corpo.get(nome, resposta.get(nome))
        return [valor] if isinstance(valor, dict) else valor

    return Resultado(str(corpo.get("codigoResultado", "")).strip(), mensaxes,
                     bloque("CUADERNO"), bloque("EXPLOTACION") or bloque("explotacionREA"))


@dataclass
class EstadoActividade:
    bloque: str
    id_ajena: int
    valida: bool
    id_cuaderno: int | None


def actividades_procesadas(resultado: Resultado) -> list[EstadoActividade]:
    """Cada actividade que a Xunta devolve en comprobarEstado, co seu esValida e IdCuaderno."""
    estados = []
    for cuaderno in resultado.cuaderno or []:
        for bloque, actividades in (cuaderno.get("ActividadesExplotacion") or {}).items():
            for actividade in actividades:
                clave = next((k for k in actividade if k.startswith("IdAjena")), None)
                if clave is None or _num(actividade[clave]) is None:
                    continue
                estados.append(EstadoActividade(bloque, int(actividade[clave]),
                                                bool(actividade.get("esValida")),
                                                _num(actividade.get("IdCuaderno"))))
    return estados


Abrir = Callable[[urllib.request.Request], Any]


class Xeaga:
    """As chamadas ao IUWS. `abrir` substitúese nas probas."""

    def __init__(self, url_base: str, app: str, abrir: Abrir | None = None) -> None:
        self.url_base = url_base.rstrip("/")
        self.app = app
        self._abrir = abrir or (lambda peticion: urllib.request.urlopen(peticion, timeout=60))

    def url_acceso(self, peticion: str) -> str:
        """Onde se manda o titular para que se identifique na Xunta (comunicacionProductor)."""
        return f"{self.url_base}/comunicacionProductor/{self.app}/{peticion}"

    def _chamar(self, ruta: str, token: Token | None = None,
                corpo: bytes | None = None) -> dict[str, Any]:
        cabeceiras = {"Accept": "application/json", "IUWS-Consumer": IUWS_CONSUMER}
        if token is not None:
            cabeceiras["Authorization"] = f"Bearer {token.valor}"
        if corpo is not None:
            cabeceiras["Content-Type"] = "application/json"
        peticion = urllib.request.Request(f"{self.url_base}/{ruta}", data=corpo,
                                          headers=cabeceiras,
                                          method="POST" if corpo is not None else "GET")
        try:
            with self._abrir(peticion) as resposta:
                texto = resposta.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise XeagaErro("A Xunta non deu acceso: volve conectar") from e
            raise XeagaErro(f"A Xunta respondeu cun erro ({e.code})") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise XeagaErro("Non se puido conectar coa Xunta") from e
        try:
            datos: dict[str, Any] = json.loads(texto) if texto.strip() else {}
        except ValueError:
            return {"codigoResultado": "OK", "version": texto.strip()}
        return datos

    def version(self) -> str:
        return str(self._chamar("version").get("version", ""))

    def exportar_rea(self, token: Token, nif: str) -> Resultado:
        # Produtor particular: sen CIF de xestora (Anexo VI §3.3)
        return ler_resultado(self._chamar(f"exportarREA/{nif}", token))

    def exportar_cue(self, token: Token, codigo_rea: str) -> Resultado:
        return ler_resultado(self._chamar(f"exportar/{codigo_rea}", token))

    def crear(self, token: Token, cuaderno: dict[str, Any]) -> int:
        """Envía o CUADERNO e devolve o número de petición para comprobar o estado."""
        corpo = json.dumps({"CUADERNO": [cuaderno]}, ensure_ascii=False).encode("utf-8")
        if len(corpo) > MAX_BYTES:
            raise XeagaErro("O envío pasa de 2 MB: envía un período máis curto")
        resultado = ler_resultado(self._chamar("crear/", token, corpo))
        peticion = resultado.mensaxes[0].codigo if resultado.mensaxes else None
        if resultado.codigo != "OK" or peticion is None:
            texto = "; ".join(m.texto for m in resultado.mensaxes) or resultado.codigo
            raise XeagaErro(f"A Xunta non aceptou o envío: {texto}")
        return peticion

    def comprobar_estado(self, token: Token, peticion: int) -> Resultado:
        return ler_resultado(self._chamar(f"comprobarEstado/{peticion}", token))
