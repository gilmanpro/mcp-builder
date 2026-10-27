# Guía de Implementación de Servidores MCP en Python

## Resumen

Este documento proporciona las mejores prácticas y ejemplos específicos de Python para implementar servidores MCP usando el SDK de Python de MCP. Cubre configuración del servidor, patrones de registro de herramientas, validación de entrada con Pydantic, manejo de errores y ejemplos completos funcionales.

---

## Referencia Rápida

### Importaciones Clave
```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
import httpx
```

### Inicialización del Servidor
```python
mcp = FastMCP("service_mcp")
```

### Patrón de Registro de Herramientas
```python
@mcp.tool(name="tool_name", annotations={...})
async def tool_function(params: InputModel) -> str:
    # Implementación
    pass
```

---

## SDK de Python para MCP y FastMCP

El SDK oficial de Python para MCP proporciona FastMCP, un framework de alto nivel para construir servidores MCP. Proporciona:
- Generación automática de descripciones y inputSchema a partir de firmas de funciones y docstrings
- Integración de modelos Pydantic para validación de entrada
- Registro de herramientas basado en decoradores con `@mcp.tool`

**Para documentación completa del SDK, usa WebFetch para cargar:**
`https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`

## FastMCP standalone (recomendado para servidores nuevos)

Existe **dos formas de usar FastMCP en Python** y confunden a mucha gente:

| Origen | Import | Cuándo |
|---|---|---|
| Paquete oficial `fastmcp` (Prefect, gofastmcp.com) | `from fastmcp import FastMCP` | **Por defecto**: cliente, apps interactivas, proxy, composición, generación desde OpenAPI/FastAPI |
| SDK oficial `mcp` (embebe FastMCP 1.0) | `from mcp.server.fastmcp import FastMCP` | Solo si ya dependes del SDK oficial y no necesitas funciones de v2+ |

Instalación y comandos (recomendado con `uv`):

```bash
uv add fastmcp            # instalar
fastmcp dev servidor.py   # probar con MCP Inspector (modo desarrollo)
fastmcp install servidor.py --name "Mi Herramienta"   # instalar en Claude Desktop
uv run python servidor.py # ejecución directa
```

Si el objeto no se llama `mcp`/`server`/`app`: `fastmcp dev modulo.py:mi_instancia`.

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("ejemplo_mcp")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Suma dos números."""
    return a + b

if __name__ == "__main__":
    mcp.run()                                 # stdio (default)
    # mcp.run(transport="http", host="127.0.0.1", port=8000)   # Streamable HTTP local
```

Funciones de v2+ que resuelven trabajo a mano:

- **Generación desde API existente**: `FastMCP.from_openapi(spec, client=httpx.AsyncClient(base_url=...))` o `FastMCP.from_fastapi(app)` — `GET` → resources, resto → tools (sobreescribible). Punto de partida ideal si la API ya está documentada.
- **Contexto**: parámetro `ctx: Context` → `ctx.info()`, `ctx.report_progress()`, `ctx.read_resource()`.
- **Composición**: `mcp.mount("github", github_mcp)` prefija tools automáticamente (`github/...`), evitando colisiones entre módulos.
- **Proxy**: `FastMCP.as_proxy(cliente)` para convertir transporte (p. ej. stdio → HTTP) o añadir logging/auth delante de un servidor existente.
- **Raíces**: el cliente declara qué directorios puede tocar el servidor; respétalos en cualquier herramienta de archivos.

Cuando la documentación de FastMCP describa la rama `main`, verifica la versión: añade `https://gofastmcp.com/<ruta>.md` a cualquier URL para leerla en Markdown (`llms.txt`/`llms-full.txt` también existen).

## Convención de Nombres de Servidores

Los servidores MCP de Python deben seguir este patrón de nomenclatura:
- **Formato**: `{servicio}_mcp` (minúsculas con guiones bajos)
- **Ejemplos**: `github_mcp`, `jira_mcp`, `stripe_mcp`

El nombre debe ser:
- General (no ligado a características específicas)
- Descriptivo del servicio/API que se integra
- Fácil de inferir de la descripción de la tarea
- Sin números de versión o fechas

## Implementación de Herramientas

### Nombres de Herramientas

Usa snake_case para los nombres de las herramientas (ej., "search_users", "create_project", "get_channel_info") con nombres claros y orientados a la acción.

**Evita Conflictos de Nombres**: Incluye el contexto del servicio para prevenir superposiciones:
- Usa "slack_send_message" en lugar de solo "send_message"
- Usa "github_create_issue" en lugar de solo "create_issue"
- Usa "asana_list_tasks" en lugar de solo "list_tasks"

### Estructura de Herramientas con FastMCP

Las herramientas se definen usando el decorador `@mcp.tool` con modelos Pydantic para validación de entrada:

```python
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example_mcp")

class ServiceToolInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    param1: str = Field(..., description="Descripción del primer parámetro", min_length=1, max_length=100)
    param2: Optional[int] = Field(default=None, description="Parámetro entero opcional", ge=0, le=1000)
    tags: Optional[List[str]] = Field(default_factory=list, description="Lista de etiquetas", max_items=10)

@mcp.tool(
    name="service_tool_name",
    annotations={
        "title": "Título Legible de la Herramienta",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def service_tool_name(params: ServiceToolInput) -> str:
    '''Descripción de la herramienta.

    Esta herramienta realiza una operación específica en el servicio.

    Args:
        params (ServiceToolInput): Parámetros de entrada validados.

    Returns:
        str: Respuesta con formato JSON.
    '''
    pass
```

## Pydantic v2 - Características Clave

- Usa `model_config` en lugar de la clase `Config` anidada
- Usa `field_validator` en lugar del obsoleto `validator`
- Usa `model_dump()` en lugar del obsoleto `dict()`
- Los validadores requieren el decorador `@classmethod`
- Los type hints son requeridos para los métodos validador

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CreateUserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: str = Field(..., description="Nombre completo del usuario", min_length=1, max_length=100)
    email: str = Field(..., description="Email del usuario", pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., description="Edad del usuario", ge=0, le=150)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El email no puede estar vacío")
        return v.lower()
```

## Opciones de Formato de Respuesta

Soporta múltiples formatos de salida para flexibilidad:

```python
from enum import Enum

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class UserSearchInput(BaseModel):
    query: str = Field(..., description="Consulta de búsqueda")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Formato de salida: 'markdown' para legible o 'json' para máquina"
    )
```

## Implementación de Paginación

Para herramientas que listan recursos:

```python
class ListInput(BaseModel):
    limit: Optional[int] = Field(default=20, description="Máximo de resultados", ge=1, le=100)
    offset: Optional[int] = Field(default=0, description="Resultados a saltar para paginación", ge=0)

async def list_items(params: ListInput) -> str:
    data = await api_request(limit=params.limit, offset=params.offset)
    import json
    response = {
        "total": data["total"],
        "count": len(data["items"]),
        "offset": params.offset,
        "items": data["items"],
        "has_more": data["total"] > params.offset + len(data["items"]),
        "next_offset": params.offset + len(data["items"]) if data["total"] > params.offset + len(data["items"]) else None
    }
    return json.dumps(response, indent=2)
```

## Manejo de Errores

Proporciona mensajes de error claros y accionables:

```python
def _handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Recurso no encontrado. Verifica el ID."
        elif e.response.status_code == 403:
            return "Error: Permiso denegado. No tienes acceso a este recurso."
        elif e.response.status_code == 429:
            return "Error: Límite de tasa excedido. Espera antes de hacer más solicitudes."
        return f"Error: Solicitud falló con estado {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Tiempo de espera agotado. Intenta de nuevo."
    return f"Error inesperado: {type(e).__name__}"
```

## Utilidades Compartidas

```python
async def _make_api_request(endpoint: str, method: str = "GET", **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method, f"{API_BASE_URL}/{endpoint}", timeout=30.0, **kwargs
        )
        response.raise_for_status()
        return response.json()
```

## Ejemplo Completo

```python
#!/usr/bin/env python3
from typing import Optional, List, Dict, Any
from enum import Enum
import httpx
import json
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example_mcp")
API_BASE_URL = "https://api.example.com/v1"

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class UserSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    query: str = Field(..., description="Cadena de búsqueda", min_length=2, max_length=200)
    limit: Optional[int] = Field(default=20, description="Máximo de resultados", ge=1, le=100)
    offset: Optional[int] = Field(default=0, description="Resultados a saltar", ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Formato de salida")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La consulta no puede estar vacía")
        return v.strip()

async def _make_api_request(endpoint: str, method: str = "GET", **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{API_BASE_URL}/{endpoint}", timeout=30.0, **kwargs)
        response.raise_for_status()
        return response.json()

def _handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Recurso no encontrado."
        elif e.response.status_code == 403:
            return "Error: Permiso denegado."
        elif e.response.status_code == 429:
            return "Error: Límite de tasa excedido."
        return f"Error: Solicitud falló con estado {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Tiempo de espera agotado."
    return f"Error inesperado: {type(e).__name__}"

@mcp.tool(name="example_search_users", annotations={
    "title": "Buscar Usuarios de Ejemplo",
    "readOnlyHint": True, "destructiveHint": False,
    "idempotentHint": True, "openWorldHint": True
})
async def example_search_users(params: UserSearchInput) -> str:
    '''Busca usuarios en el sistema de Ejemplo por nombre, email o equipo.

    Args:
        params (UserSearchInput): Parámetros de entrada validados.

    Returns:
        str: Resultados formateados como JSON o Markdown.
    '''
    try:
        data = await _make_api_request("users/search", params={
            "q": params.query, "limit": params.limit, "offset": params.offset
        })
        users = data.get("users", [])
        total = data.get("total", 0)
        if not users:
            return f"No se encontraron usuarios para '{params.query}'"
        response = {"total": total, "count": len(users), "offset": params.offset, "users": users}
        return json.dumps(response, indent=2)
    except Exception as e:
        return _handle_api_error(e)

if __name__ == "__main__":
    mcp.run()
```

---

## Características Avanzadas de FastMCP

### Inyección de Parámetros de Contexto

FastMCP puede inyectar automáticamente un parámetro `Context` en las herramientas:

```python
from mcp.server.fastmcp import FastMCP, Context

@mcp.tool()
async def advanced_search(query: str, ctx: Context) -> str:
    await ctx.report_progress(0.25, "Iniciando búsqueda...")
    results = await search_api(query)
    await ctx.report_progress(0.75, "Formateando resultados...")
    return format_results(results)
```

### Registro de Recursos

```python
@mcp.resource("file://documents/{name}")
async def get_document(name: str) -> str:
    with open(f"./docs/{name}", "r") as f:
        return f.read()
```

### Gestión de Ciclo de Vida

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan():
    db = await connect_to_database()
    yield {"db": db}
    await db.close()

mcp = FastMCP("example_mcp", lifespan=app_lifespan)
```

### Opciones de Transporte

```python
# stdio (predeterminado)
if __name__ == "__main__":
    mcp.run()

# Streamable HTTP
if __name__ == "__main__":
    mcp.run(transport="streamable_http", port=8000)
```

---

## Lista de Verificación de Calidad

### Diseño Estratégico
- [ ] Las herramientas habilitan flujos de trabajo completos
- [ ] Los nombres reflejan subdivisiones naturales de tareas

### Calidad de Implementación
- [ ] Herramientas más importantes y valiosas implementadas
- [ ] Todas las herramientas tienen nombres y documentación descriptivos
- [ ] El nombre del servidor sigue el formato: `{servicio}_mcp`
- [ ] Todas las operaciones de red usan async/await

### Configuración de Herramientas
- [ ] Todas las herramientas implementan 'name' y 'annotations' en el decorador
- [ ] Anotaciones correctamente configuradas
- [ ] Usan Pydantic BaseModel para validación de entrada con Field()
- [ ] Docstrings completos con tipos de entrada/salida explícitos

### Calidad de Código
- [ ] Importaciones adecuadas incluyendo Pydantic
- [ ] Paginación implementada donde corresponda
- [ ] Funciones asíncronas definidas con `async def`
- [ ] Type hints usados en todo el código
- [ ] Constantes definidas a nivel de módulo en MAYÚSCULAS
