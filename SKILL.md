---
name: mcp-builder
description: "Crea, rediseña y asegura servidores MCP (Model Context Protocol) en Python (FastMCP) o TypeScript que exponen APIs, datos y acciones como tools, resources y prompts para LLMs: diseño de herramientas y esquemas, transporte stdio vs Streamable HTTP, autenticación OAuth 2.1, secretos, validación de entrada, rate limiting, pruebas con MCP Inspector, evaluaciones y despliegue. Usar SIEMPRE que el usuario quiera crear, integrar, desplegar, auditar o depurar un servidor MCP, conectar una API externa a un asistente o agente IA, o evaluar la seguridad de un servidor MCP existente."
---

# MCP Builder

Construye servidores MCP seguros que expongan APIs y datos existentes como herramientas que los LLMs puedan descubrir e invocar.

## Primero: ¿MCP o API directa?

No crees un servidor MCP por defecto (marco Jitterbit):

- **API directa basta** cuando hay pocos agentes, flujos estables, capacidades no compartidas y un solo equipo propietario.
- **MCP gana** cuando las mismas capacidades las consumen varios agentes/equipos, las integraciones se duplican, o necesitas descubrimiento estándar y orquestación multiagente.
- Un MCP **no sustituye a las APIs**: las consume. Diseña capacidades para agentes, no replicando endpoints (`search_customer`, no `execute_function_7`).

## Flujo de trabajo

1. **Decide** (árbol anterior) y elige transporte con la tabla de abajo.
2. **Diseña** las herramientas: nombres, esquemas, anotaciones y formato de respuesta (ver reglas más abajo).
3. **Implementa** con la plantilla segura: `python scripts/crear_servidor.py <nombre> [--http]` genera un esqueleto con defaults seguros; completa la lógica de negocio.
4. **Asegura**: pasa el gate de seguridad de la sección siguiente (obligatorio antes de entregar).
5. **Prueba** con MCP Inspector y **evalúa** con evaluaciones (ver triggers de referencias al final).

## Transporte

| Criterio | stdio | Streamable HTTP |
|---|---|---|
| Despliegue | Local, un usuario | Remoto, multi-cliente |
| Seguridad | Aislamiento de proceso; datos no salen de la máquina | Requiere TLS + OAuth 2.1 + validación de `Origin` |
| Complejidad | Baja | Media |

- **stdio** por defecto para integraciones locales; jamás imprimir logs en stdout (usa stderr).
- **Streamable HTTP** para servicios web/remotos. Enlaza a `127.0.0.1`, nunca a `0.0.0.0`, si es local.
- **SSE está obsoleto** en favor de Streamable HTTP; no lo uses en servidores nuevos.

## Reglas de diseño de herramientas

- **Nombres**: `{servicio}_{acción}_{recurso}` en snake_case, verbos al inicio (`github_create_issue`). El prefijo evita colisiones con otros servidores MCP cargados a la vez.
- **Esquemas**: Pydantic (Python) o Zod `.strict()` (TypeScript) en TODA entrada, con `description`, límites (`min/max`, `ge/le`) y sin campos extra.
- **Anotaciones**: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` siempre; una herramienta destructiva lleva interfaz explícita y confirmación.
- **Respuesta**: JSON para procesamiento del agente, Markdown para lectura; paginación con `limit` (default 20-50), `offset`/`cursor`, `has_more`, `next_offset`, `total_count`. Nunca cargues listas completas en memoria.
- **Contrato**: entradas y salidas predecibles; los cambios de nombre, esquema o permisos de una herramienta son cambios de API: versiona y documenta.
- **Errores**: mensaje accionable con próximo paso (`Error: límite de tasa excedido. Espera 30s.`), `isError: true`, sin filtrar stack traces ni detalles internos.

## Gate de seguridad (obligatorio antes de entregar)

MCP **no trae autenticación, autorización ni cifrado nativos** (Cloudflare): todo esto lo implementas tú. Lee `reference/seguridad.md` (imprescindible) y verifica:

- [ ] Credenciales solo por variables de entorno o gestor de secretos; jamás en código, logs ni respuestas.
- [ ] Toda entrada validada por esquema; paths de archivo canónicos dentro de una raíz permitida (anti directory traversal); sin construcción de comandos con datos de usuario.
- [ ] Red con lista blanca de destinos; sin fetch de URLs arbitrarias por parte del servidor.
- [ ] HTTP remoto: TLS, OAuth 2.1 con validación de audiencia (token emitido PARA este servidor), validación de `Origin`, rate limiting por usuario/herramienta.
- [ ] Logs estructurados de auditoría en stderr/archivo (herramienta invocada, quién, resultado), sin secretos.
- [ ] Menor privilegio: herramientas destructivas separadas de las de solo lectura; el servidor no debe eludir los controles de autorización de la API subyacente.

## Implementación

| Lenguaje | Guía | SDK/CLI |
|---|---|---|
| Python | `reference/python_mcp_server.md` | `fastmcp` (recomendado: `uv add fastmcp`) o SDK oficial `mcp` |
| TypeScript | `reference/node_mcp_server.md` | `@modelcontextprotocol/sdk` + Zod |

Python rápido: `fastmcp dev servidor.py` (Inspector), `fastmcp install servidor.py` (Claude Desktop). TypeScript: `npm run build` y `npx @modelcontextprotocol/inspector`.

## Anti-patrones (y por qué)

- *Replicar endpoints de la API tal cual* → el agente no sabe combinarlos; expone implementación en vez de capacidades.
- *Herramientas con nombres genéricos (`run_query`)* → colisionan con otros servidores y el modelo elige mal.
- *Secretos en variables de entorno planas leídas al inicio y volcados en errores* → fuga de credenciales en listas de procesos y logs (66% de servidores analizados tienen malas prácticas de este tipo).
- *Confiar en la descripción de una herramienta remota* → tool poisoning: un servidor malicioso reescribe sus descripciones para manipular al agente; valida y registra cambios.
- *Anotaciones como garantía de seguridad* → son sugerencias para el cliente, no un control; la autorización se verifica en cada solicitud.
- *Exponer `0.0.0.0` en local "para que funcione"* → convierte tu laptop en endpoint accesible (DNS rebinding/on-path); usa `127.0.0.1` y valida `Origin`.

## Evaluaciones

Diseña 10 preguntas realistas, de solo lectura, independientes, no destructivas, con respuesta única, verificable y estable. Formato XML `<evaluation>`/`<qa_pair>`; ver `reference/evaluation.md` y ejecuta `scripts/evaluation.py`.

## Referencias (cuándo leerlas)

- `reference/seguridad.md` — **SIEMPRE antes de entregar** un servidor o al auditar uno existente: 6 vectores de ataque, OAuth/tokens, secretos, red, logs, cadena de suministro.
- `reference/mcp_best_practices.md` — al **diseñar** herramientas/nombres/paginación o **decidir transporte**; incluye cuándo MCP vs API y gobernanza como infraestructura compartida.
- `reference/python_mcp_server.md` — solo al **implementar en Python** (FastMCP, Pydantic, OpenAPI→MCP).
- `reference/node_mcp_server.md` — solo al **implementar en TypeScript** (registerTool, Zod, estructura de proyecto).
- `reference/evaluation.md` — solo al **crear o ejecutar evaluaciones** del servidor.
