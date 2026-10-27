# mcp-builder

Crea, redisena y asegura **servidores MCP** (Model Context Protocol) en Python (FastMCP) o TypeScript: diseno de tools/resources/prompts y esquemas, transporte stdio vs Streamable HTTP, autenticacion OAuth 2.1, gestion de secretos, validacion y evaluacion.

Skill para [OpenCode](https://opencode.ai) bajo el estandar [Agent Skills](https://agentskills.io) (compatible con `.opencode/skills/`, `.claude/skills/` y `.agents/skills/`). Documentacion y cuerpo completos en `SKILL.md`; este repo es un espejo publico de la skill.

## Instalacion

```bash
cmdc skills add gilmanpro/mcp-builder -g      # Command Code
```

Manual (OpenCode u otro arnes): copia esta carpeta a `~/.agents/skills/mcp-builder/` (global) o `<proyecto>/.opencode/skills/mcp-builder/`.

## Contenido

- `SKILL.md` — flujo de construccion y buenas practicas
- `reference/` — MCP en Python y Node, mejores practicas, seguridad, evaluacion
- `scripts/` — `crear_servidor.py`, `connections.py`, `evaluation.py`

## Verificacion

```bash
python skill-creator/scripts/quick_validate.py mcp-builder
python skill-creator/scripts/auditar_seguridad.py mcp-builder
```

Issues y PRs de mejora bienvenidos.
