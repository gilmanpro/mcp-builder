#!/usr/bin/env python3
"""Genera un esqueleto de servidor MCP con defaults seguros (stdlib puro).

Uso:
    python crear_servidor.py github                 # stdio -> github_mcp.py
    python crear_servidor.py slack --http --puerto 8000
    python crear_servidor.py jira --salida ./src

El fichero generado usa FastMCP (uv add fastmcp). El generador no ejecuta
red ni instala dependencias.
"""

import argparse
import re
import sys
from pathlib import Path

VALIDO = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")

PLANTILLA = '''#!/usr/bin/env python3
"""Servidor MCP __NOMBRE__ (transporte: __TRANSPORTE__).

Esqueleto generado con defaults seguros por mcp-builder.
Pendiente: completar la logica de negocio y pasar el gate de
seguridad de reference/seguridad.md antes de desplegar.
"""

import json
import os
import sys
import time
from collections import deque
from enum import Enum
from typing import Optional

from fastmcp import FastMCP
from pydantic import ConfigDict, Field, field_validator
from pydantic import BaseModel

SERVICIO = "__SERVICIO__"
API_BASE_URL = os.environ.get(f"{SERVICIO.upper()}_API_BASE_URL", "https://api.__SERVICIO__.example.com/v1")
TIMEOUT = 30
CHARACTER_LIMIT = 25000
PAGE_DEFAULT = 20
PAGE_MAX = 100
RATE_LIMIT = 30
RATE_WINDOW = 60


def requerir_secreto(nombre: str) -> str:
    valor = os.environ.get(nombre, "")
    if not valor:
        sys.exit(f"Falta la variable de entorno {nombre} (nunca hardcodees el secreto)")
    return valor


API_TOKEN = requerir_secreto(f"{SERVICIO.upper()}_API_TOKEN")

_llamadas = deque()


def limitar_tasa() -> Optional[str]:
    ahora = time.monotonic()
    while _llamadas and ahora - _llamadas[0] > RATE_WINDOW:
        _llamadas.popleft()
    if len(_llamadas) >= RATE_LIMIT:
        return f"Limite de tasa excedido ({RATE_LIMIT} llamadas/{RATE_WINDOW}s). Espera antes de repetir."
    _llamadas.append(ahora)
    return None


class FormatoRespuesta(str, Enum):
    markdown = "markdown"
    json = "json"


class BusquedaEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query: str = Field(..., description="Texto a buscar", min_length=2, max_length=200)
    limit: int = Field(default=PAGE_DEFAULT, description="Maximo de resultados", ge=1, le=PAGE_MAX)
    offset: int = Field(default=0, description="Resultados a saltar (paginacion)", ge=0)
    response_format: FormatoRespuesta = Field(
        default=FormatoRespuesta.markdown,
        description="markdown para lectura, json para procesamiento del agente",
    )

    @field_validator("query")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v:
            raise ValueError("La consulta no puede estar vacia")
        return v


def manejar_error(exc: Exception) -> str:
    estado = getattr(getattr(exc, "response", None), "status_code", None)
    mensajes = {
        401: "Autenticacion fallida. Verifica el token configurado.",
        403: "Permiso denegado para este recurso.",
        404: "Recurso no encontrado. Verifica el identificador.",
        429: "Limite de la API alcanzado. Espera y reintenta.",
    }
    if estado in mensajes:
        return mensajes[estado]
    if exc.__class__.__name__ == "TimeoutException":
        return "Tiempo de espera agotado. Reintenta con un limit menor."
    sys.stderr.write(f"error interno en {SERVICIO}_mcp: {exc!r}\\n")
    return "Error interno al consultar el servicio. Detalle registrado en el servidor (stderr)."


def paginar(datos: list, total: int, offset: int) -> str:
    sigue = total > offset + len(datos)
    return json.dumps(
        {
            "total": total,
            "count": len(datos),
            "offset": offset,
            "items": datos,
            "has_more": sigue,
            "next_offset": offset + len(datos) if sigue else None,
        },
        ensure_ascii=False,
        indent=2,
    )


mcp = FastMCP("__NOMBRE__")


@mcp.tool(
    name="__SERVICIO___search",
    annotations={
        "title": "Buscar en __SERVICIO__",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def buscar(params: BusquedaEntrada) -> str:
    """Busca registros en __SERVICIO__ por texto libre, con paginacion.

    Args:
        params: consulta, paginacion y formato de respuesta.

    Returns:
        JSON con items, total, has_more y next_offset.
    """
    error = limitar_tasa()
    if error:
        return error
    try:
        import httpx

        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            respuesta = await cliente.get(
                f"{API_BASE_URL}/search",
                params={"q": params.query, "limit": params.limit, "offset": params.offset},
                headers={"Authorization": f"Bearer {API_TOKEN}"},
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
        items = datos.get("items", [])
        texto = paginar(items, datos.get("total", len(items)), params.offset)
        if len(texto) > CHARACTER_LIMIT:
            return (
                f"Respuesta truncada a {params.limit // 2} elementos. "
                "Usa offset o agrega filtros para acotar."
            )
        return texto
    except Exception as exc:
        return manejar_error(exc)


if __name__ == "__main__":
__EJECUCION__
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un servidor MCP con defaults seguros")
    parser.add_argument("nombre", help="servicio o dominio (p. ej. github, jira_mcp)")
    parser.add_argument("--http", action="store_true", help="transporte Streamable HTTP en 127.0.0.1 (default: stdio)")
    parser.add_argument("--puerto", type=int, default=8000, help="puerto para --http (default: 8000)")
    parser.add_argument("--salida", default=".", help="directorio destino (default: actual)")
    args = parser.parse_args()

    servicio = args.nombre.lower().removesuffix("_mcp").removesuffix("-mcp-server")
    if not VALIDO.match(servicio):
        print(f"Nombre invalido: {servicio!r}. Usa snake_case: [a-z0-9] con guiones bajos.", file=sys.stderr)
        return 2

    nombre = f"{servicio}_mcp"
    if args.http:
        ejecucion = (
            f'    mcp.run(transport="http", host="127.0.0.1", port={args.puerto})\n'
            "    # Enlace solo a loopback: exponer en otra interfaz exige TLS + OAuth 2.1\n"
            "    # y validacion de Origin (ver reference/seguridad.md)."
        )
        transporte = f"Streamable HTTP en 127.0.0.1:{args.puerto}"
    else:
        ejecucion = "    mcp.run()  # stdio: los logs van a stderr, jamas a stdout"
        transporte = "stdio"

    contenido = (
        PLANTILLA.replace("__NOMBRE__", nombre)
        .replace("__SERVICIO__", servicio)
        .replace("__TRANSPORTE__", transporte)
        .replace("__EJECUCION__", ejecucion)
    )

    destino = Path(args.salida) / f"{nombre}.py"
    if destino.exists():
        print(f"Ya existe {destino}; no lo sobrescribo.", file=sys.stderr)
        return 1
    destino.write_text(contenido, encoding="utf-8")

    print(f"Creado {destino}")
    print(f"Siguiente: uv add fastmcp httpx  |  fastmcp dev {destino}")
    print(f"Configura {servicio.upper()}_API_TOKEN en el entorno (nunca en el codigo) "
          "y pasa el gate de reference/seguridad.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
