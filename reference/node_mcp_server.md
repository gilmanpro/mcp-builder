# Guía de Implementación de Servidores MCP en Node/TypeScript

## Resumen

Este documento proporciona las mejores prácticas y ejemplos específicos de Node/TypeScript para implementar servidores MCP usando el SDK de TypeScript de MCP. Cubre estructura del proyecto, configuración del servidor, patrones de registro de herramientas, validación de entrada con Zod, manejo de errores y ejemplos completos funcionales.

---

## Referencia Rápida

### Importaciones Clave
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import express from "express";
import { z } from "zod";
```

### Inicialización del Servidor
```typescript
const server = new McpServer({
  name: "service-mcp-server",
  version: "1.0.0"
});
```

### Patrón de Registro de Herramientas
```typescript
server.registerTool(
  "tool_name",
  {
    title: "Nombre Mostrado de la Herramienta",
    description: "Lo que hace la herramienta",
    inputSchema: { param: z.string() },
    outputSchema: { result: z.string() }
  },
  async ({ param }) => {
    const output = { result: `Procesado: ${param}` };
    return {
      content: [{ type: "text", text: JSON.stringify(output) }],
      structuredContent: output // Patrón moderno para datos estructurados
    };
  }
);
```

---

## SDK de TypeScript para MCP

El SDK oficial de TypeScript para MCP proporciona:
- Clase `McpServer` para inicialización del servidor
- Método `registerTool` para registro de herramientas
- Integración de esquemas Zod para validación de entrada en tiempo de ejecución
- Implementaciones de manejadores de herramientas con seguridad de tipos

**IMPORTANTE - Usa Solo APIs Modernas:**
- **USA**: `server.registerTool()`, `server.registerResource()`, `server.registerPrompt()`
- **NO USES**: APIs antiguas y obsoletas como `server.tool()`, `server.setRequestHandler(ListToolsRequestSchema, ...)` o registro manual de manejadores
- Los métodos `register*` proporcionan mejor seguridad de tipos, manejo automático de esquemas y son el enfoque recomendado

Consulta la documentación del SDK de MCP en las referencias para detalles completos.

## Convención de Nombres de Servidores

Los servidores MCP de Node/TypeScript deben seguir este patrón de nomenclatura:
- **Formato**: `{servicio}-mcp-server` (minúsculas con guiones)
- **Ejemplos**: `github-mcp-server`, `jira-mcp-server`, `stripe-mcp-server`

El nombre debe ser:
- General (no ligado a características específicas)
- Descriptivo del servicio/API que se integra
- Fácil de inferir de la descripción de la tarea
- Sin números de versión o fechas

## Estructura del Proyecto

Crea la siguiente estructura para servidores MCP en Node/TypeScript:

```
{servicio}-mcp-server/
├── package.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts          # Punto de entrada principal con inicialización de McpServer
│   ├── types.ts          # Definiciones de tipos e interfaces de TypeScript
│   ├── tools/            # Implementaciones de herramientas (un archivo por dominio)
│   ├── services/         # Clientes API y utilidades compartidas
│   ├── schemas/          # Esquemas de validación Zod
│   └── constants.ts      # Constantes compartidas (API_URL, CHARACTER_LIMIT, etc.)
└── dist/                 # Archivos JavaScript compilados (punto de entrada: dist/index.js)
```

## Implementación de Herramientas

### Nombres de Herramientas

Usa snake_case para los nombres de las herramientas (ej., "search_users", "create_project", "get_channel_info") con nombres claros y orientados a la acción.

**Evita Conflictos de Nombres**: Incluye el contexto del servicio para prevenir superposiciones:
- Usa "slack_send_message" en lugar de solo "send_message"
- Usa "github_create_issue" en lugar de solo "create_issue"
- Usa "asana_list_tasks" en lugar de solo "list_tasks"

### Estructura de las Herramientas

Las herramientas se registran usando el método `registerTool` con los siguientes requisitos:
- Usa esquemas Zod para validación de entrada en tiempo de ejecución y seguridad de tipos
- El campo `description` debe proporcionarse explícitamente - los comentarios JSDoc NO se extraen automáticamente
- Proporciona explícitamente `title`, `description`, `inputSchema` y `annotations`
- El `inputSchema` debe ser un objeto de esquema Zod (no un esquema JSON)
- Tipifica todos los parámetros y valores de retorno explícitamente

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "example-mcp",
  version: "1.0.0"
});

// Esquema Zod para validación de entrada
const UserSearchInputSchema = z.object({
  query: z.string()
    .min(2, "La consulta debe tener al menos 2 caracteres")
    .max(200, "La consulta no debe exceder 200 caracteres")
    .describe("Cadena de búsqueda para coincidir con nombres/emails"),
  limit: z.number()
    .int()
    .min(1)
    .max(100)
    .default(20)
    .describe("Máximo de resultados a devolver"),
  offset: z.number()
    .int()
    .min(0)
    .default(0)
    .describe("Número de resultados a saltar para paginación"),
  response_format: z.nativeEnum(ResponseFormat)
    .default(ResponseFormat.MARKDOWN)
    .describe("Formato de salida: 'markdown' para legible o 'json' para máquina")
}).strict();

// Definición de tipo a partir del esquema Zod
type UserSearchInput = z.infer<typeof UserSearchInputSchema>;

server.registerTool(
  "example_search_users",
  {
    title: "Buscar Usuarios de Ejemplo",
    description: `Busca usuarios en el sistema de Ejemplo por nombre, email o equipo.

Esta herramienta busca en todos los perfiles de usuario de la plataforma Ejemplo, soportando coincidencias parciales y varios filtros de búsqueda. NO crea ni modifica usuarios, solo busca los existentes.

Args:
  - query (string): Cadena de búsqueda para coincidir con nombres/emails
  - limit (number): Máximo de resultados a devolver, entre 1-100 (predet: 20)
  - offset (number): Resultados a saltar para paginación (predet: 0)
  - response_format ('markdown' | 'json'): Formato de salida (predet: 'markdown')

Devuelve:
  Para JSON: Datos estructurados con esquema:
  {
    "total": number,
    "count": number,
    "offset": number,
    "users": [{ "id": string, "name": string, "email": string, "team": string, "active": boolean }],
    "has_more": boolean,
    "next_offset": number
  }

Ejemplos:
  - Usa cuando: "Encuentra todos los miembros del equipo de marketing"
  - Usa cuando: "Busca la cuenta de Juan"
  - No uses cuando: Necesitas crear un usuario (usa example_create_user en su lugar)

Manejo de Errores:
  - Devuelve "Error: Límite de tasa excedido" si hay demasiadas solicitudes
  - Devuelve "No se encontraron usuarios coincidiendo con '<query>'" si la búsqueda no da resultados`,
    inputSchema: UserSearchInputSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: true
    }
  },
  async (params: UserSearchInput) => {
    try {
      const data = await makeApiRequest<any>(
        "users/search", "GET", undefined,
        { q: params.query, limit: params.limit, offset: params.offset }
      );

      const users = data.users || [];
      const total = data.total || 0;

      if (!users.length) {
        return { content: [{ type: "text", text: `No se encontraron usuarios coincidiendo con '${params.query}'` }] };
      }

      const output = {
        total, count: users.length, offset: params.offset,
        users: users.map((user: any) => ({
          id: user.id, name: user.name, email: user.email,
          ...(user.team ? { team: user.team } : {}),
          active: user.active ?? true
        })),
        has_more: total > params.offset + users.length,
        ...(total > params.offset + users.length ? { next_offset: params.offset + users.length } : {})
      };

      let textContent: string;
      if (params.response_format === ResponseFormat.MARKDOWN) {
        const lines = [`# Resultados de Búsqueda de Usuarios: '${params.query}'`, "",
          `Encontrados ${total} usuarios (mostrando ${users.length})`, ""];
        for (const user of users) {
          lines.push(`## ${user.name} (${user.id})`);
          lines.push(`- **Email**: ${user.email}`);
          if (user.team) lines.push(`- **Equipo**: ${user.team}`);
          lines.push("");
        }
        textContent = lines.join("\n");
      } else {
        textContent = JSON.stringify(output, null, 2);
      }

      return {
        content: [{ type: "text", text: textContent }],
        structuredContent: output
      };
    } catch (error) {
      return { content: [{ type: "text", text: handleApiError(error) }] };
    }
  }
);
```

## Esquemas Zod para Validación de Entrada

Zod proporciona validación de tipos en tiempo de ejecución:

```typescript
import { z } from "zod";

// Esquema básico con validación
const CreateUserSchema = z.object({
  name: z.string()
    .min(1, "El nombre es requerido")
    .max(100, "El nombre no debe exceder 100 caracteres"),
  email: z.string()
    .email("Formato de email inválido"),
  age: z.number()
    .int("La edad debe ser un número entero")
    .min(0, "La edad no puede ser negativa")
    .max(150, "La edad no puede ser mayor a 150")
}).strict();  // Usa .strict() para prohibir campos adicionales

// Enums
enum ResponseFormat {
  MARKDOWN = "markdown",
  JSON = "json"
}

const SearchSchema = z.object({
  response_format: z.nativeEnum(ResponseFormat)
    .default(ResponseFormat.MARKDOWN)
    .describe("Formato de salida")
});

// Campos opcionales con valores predeterminados
const PaginationSchema = z.object({
  limit: z.number().int().min(1).max(100).default(20).describe("Máximo de resultados"),
  offset: z.number().int().min(0).default(0).describe("Resultados a saltar")
});
```

## Opciones de Formato de Respuesta

Soporta múltiples formatos de salida para flexibilidad:

```typescript
enum ResponseFormat {
  MARKDOWN = "markdown",
  JSON = "json"
}

const inputSchema = z.object({
  query: z.string(),
  response_format: z.nativeEnum(ResponseFormat)
    .default(ResponseFormat.MARKDOWN)
    .describe("Formato de salida: 'markdown' para legible o 'json' para máquina")
});
```

**Formato Markdown**:
- Usa encabezados, listas y formato para claridad
- Convierte marcas de tiempo a formato legible por humanos
- Muestra nombres para mostrar con IDs entre paréntesis
- Omite metadatos verbosos
- Agrupa información relacionada lógicamente

**Formato JSON**:
- Devuelve datos completos y estructurados adecuados para procesamiento programático
- Incluye todos los campos disponibles y metadatos
- Usa nombres y tipos de campo consistentes

## Implementación de Paginación

Para herramientas que listan recursos:

```typescript
const ListSchema = z.object({
  limit: z.number().int().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0)
});

async function listItems(params: z.infer<typeof ListSchema>) {
  const data = await apiRequest(params.limit, params.offset);

  const response = {
    total: data.total,
    count: data.items.length,
    offset: params.offset,
    items: data.items,
    has_more: data.total > params.offset + data.items.length,
    next_offset: data.total > params.offset + data.items.length
      ? params.offset + data.items.length
      : undefined
  };

  return JSON.stringify(response, null, 2);
}
```

## Límites de Caracteres y Truncamiento

Agrega una constante CHARACTER_LIMIT para evitar respuestas abrumadoras:

```typescript
// A nivel de módulo en constants.ts
export const CHARACTER_LIMIT = 25000;

async function searchTool(params: SearchInput) {
  let result = generateResponse(data);

  if (result.length > CHARACTER_LIMIT) {
    const truncatedData = data.slice(0, Math.max(1, data.length / 2));
    response.data = truncatedData;
    response.truncated = true;
    response.truncation_message =
      `Respuesta truncada de ${data.length} a ${truncatedData.length} elementos. ` +
      `Usa el parámetro 'offset' o agrega filtros para ver más resultados.`;
    result = JSON.stringify(response, null, 2);
  }

  return result;
}
```

## Manejo de Errores

Proporciona mensajes de error claros y accionables:

```typescript
import axios, { AxiosError } from "axios";

function handleApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    if (error.response) {
      switch (error.response.status) {
        case 404:
          return "Error: Recurso no encontrado. Verifica que el ID sea correcto.";
        case 403:
          return "Error: Permiso denegado. No tienes acceso a este recurso.";
        case 429:
          return "Error: Límite de tasa excedido. Espera antes de hacer más solicitudes.";
        default:
          return `Error: La solicitud a la API falló con estado ${error.response.status}`;
      }
    } else if (error.code === "ECONNABORTED") {
      return "Error: La solicitud agotó el tiempo de espera. Intenta de nuevo.";
    }
  }
  return `Error: Ocurrió un error inesperado: ${error instanceof Error ? error.message : String(error)}`;
}
```

## Utilidades Compartidas

Extrae funcionalidad común en funciones reutilizables:

```typescript
async function makeApiRequest<T>(
  endpoint: string, method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
  data?: any, params?: any
): Promise<T> {
  try {
    const response = await axios({
      method, url: `${API_BASE_URL}/${endpoint}`, data, params,
      timeout: 30000,
      headers: { "Content-Type": "application/json", "Accept": "application/json" }
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}
```

## Mejores Prácticas de Async/Await

Usa siempre async/await para solicitudes de red y operaciones de I/O:

```typescript
// Bueno: Solicitud de red asíncrona
async function fetchData(resourceId: string): Promise<ResourceData> {
  const response = await axios.get(`${API_URL}/resource/${resourceId}`);
  return response.data;
}

// Malo: Cadenas de Promesas
function fetchData(resourceId: string): Promise<ResourceData> {
  return axios.get(`${API_URL}/resource/${resourceId}`)
    .then(response => response.data);  // Más difícil de leer y mantener
}
```

## Mejores Prácticas de TypeScript

1. **Usa TypeScript estricto**: Habilita strict mode en tsconfig.json
2. **Define Interfaces**: Crea definiciones de interfaz claras para todas las estructuras de datos
3. **Evita `any`**: Usa tipos adecuados o `unknown` en lugar de `any`
4. **Zod para Validación en Tiempo de Ejecución**: Usa esquemas Zod para validar datos externos
5. **Type Guards**: Crea funciones type guard para verificación de tipos compleja
6. **Manejo de Errores**: Usa siempre try-catch con verificación de tipo de error adecuada
7. **Seguridad de Nulos**: Usa encadenamiento opcional (`?.`) y coalescencia nula (`??`)

```typescript
// Bueno: Seguridad de tipos con Zod e interfaces
interface UserResponse {
  id: string; name: string; email: string; team?: string; active: boolean;
}

const UserSchema = z.object({
  id: z.string(), name: z.string(), email: z.string().email(),
  team: z.string().optional(), active: z.boolean()
});

type User = z.infer<typeof UserSchema>;

async function getUser(id: string): Promise<User> {
  const data = await apiCall(`/users/${id}`);
  return UserSchema.parse(data);
}

// Malo: Usando any
async function getUser(id: string): Promise<any> {
  return await apiCall(`/users/${id}`);
}
```

## Configuración de Paquetes

### package.json

```json
{
  "name": "{servicio}-mcp-server",
  "version": "1.0.0",
  "description": "Servidor MCP para integración con API de {Servicio}",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "clean": "rm -rf dist"
  },
  "engines": { "node": ">=18" },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.6.1",
    "axios": "^1.7.9",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.10.0",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "allowSyntheticDefaultImports": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Ejemplo Completo

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import axios, { AxiosError } from "axios";
import express from "express";

const API_BASE_URL = "https://api.example.com/v1";
const CHARACTER_LIMIT = 25000;

enum ResponseFormat { MARKDOWN = "markdown", JSON = "json" }

const UserSearchInputSchema = z.object({
  query: z.string().min(2).max(200).describe("Cadena de búsqueda"),
  limit: z.number().int().min(1).max(100).default(20).describe("Máximo de resultados"),
  offset: z.number().int().min(0).default(0).describe("Resultados a saltar"),
  response_format: z.nativeEnum(ResponseFormat).default(ResponseFormat.MARKDOWN).describe("Formato de salida")
}).strict();

type UserSearchInput = z.infer<typeof UserSearchInputSchema>;

async function makeApiRequest<T>(endpoint: string, method = "GET" as const, data?: any, params?: any): Promise<T> {
  const response = await axios({ method, url: `${API_BASE_URL}/${endpoint}`, data, params, timeout: 30000,
    headers: { "Content-Type": "application/json", "Accept": "application/json" } });
  return response.data;
}

function handleApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    if (error.response) {
      switch (error.response.status) {
        case 404: return "Error: Recurso no encontrado. Verifica el ID.";
        case 403: return "Error: Permiso denegado.";
        case 429: return "Error: Límite de tasa excedido. Espera antes de hacer más solicitudes.";
        default: return `Error: Solicitud falló con estado ${error.response.status}`;
      }
    }
    if (error.code === "ECONNABORTED") return "Error: Tiempo de espera agotado. Intenta de nuevo.";
  }
  return `Error inesperado: ${error instanceof Error ? error.message : String(error)}`;
}

const server = new McpServer({ name: "example-mcp", version: "1.0.0" });

server.registerTool("example_search_users", {
  title: "Buscar Usuarios de Ejemplo",
  description: "Busca usuarios por nombre, email o equipo.",
  inputSchema: UserSearchInputSchema,
  annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true }
}, async (params: UserSearchInput) => {
  try {
    const data = await makeApiRequest<any>("users/search", "GET", undefined, { q: params.query, limit: params.limit, offset: params.offset });
    const users = data.users || [];
    const total = data.total || 0;
    if (!users.length) return { content: [{ type: "text", text: `No se encontraron usuarios para '${params.query}'` }] };
    // ... resto de la implementación
    return { content: [{ type: "text", text: JSON.stringify({ total, count: users.length, offset: params.offset, users }) }] };
  } catch (error) {
    return { content: [{ type: "text", text: handleApiError(error) }] };
  }
});

async function runStdio() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

async function runHTTP() {
  const app = express();
  app.use(express.json());
  app.post('/mcp', async (req, res) => {
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
    res.on('close', () => transport.close());
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  });
  const port = parseInt(process.env.PORT || '3000');
  app.listen(port, () => console.error(`Servidor MCP en http://localhost:${port}/mcp`));
}

const transport = process.env.TRANSPORT || 'stdio';
if (transport === 'http') runHTTP().catch(e => { console.error("Error:", e); process.exit(1); });
else runStdio().catch(e => { console.error("Error:", e); process.exit(1); });
```

---

## Características Avanzadas de MCP

### Registro de Recursos

Expón datos como recursos para acceso eficiente basado en URI:

```typescript
import { ResourceTemplate } from "@modelcontextprotocol/sdk/types.js";

server.registerResource({
  uri: "file://documents/{name}",
  name: "Recurso de Documento",
  description: "Accede a documentos por nombre",
  mimeType: "text/plain"
}, async (uri: string) => {
  const match = uri.match(/^file:\/\/documents\/(.+)$/);
  if (!match) throw new Error("Formato de URI inválido");
  const content = await loadDocument(match[1]);
  return { contents: [{ uri, mimeType: "text/plain", text: content }] };
});
```

### Opciones de Transporte

#### Streamable HTTP (Recomendado para Servidores Remotos)

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

app.post('/mcp', async (req, res) => {
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true });
  res.on('close', () => transport.close());
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
```

#### stdio (Para Integraciones Locales)

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## Lista de Verificación de Calidad

### Diseño Estratégico
- [ ] Las herramientas habilitan flujos de trabajo completos
- [ ] Los nombres reflejan subdivisiones naturales de tareas
- [ ] Los formatos de respuesta optimizan la eficiencia del contexto del agente

### Calidad de Implementación
- [ ] Herramientas más importantes y valiosas implementadas
- [ ] Todas las herramientas usan `registerTool` con configuración completa
- [ ] Anotaciones correctamente configuradas
- [ ] Esquemas Zod con restricciones y mensajes de error descriptivos

### Calidad de TypeScript
- [ ] Interfaces definidas para todas las estructuras de datos
- [ ] TypeScript estricto habilitado en tsconfig.json
- [ ] Sin uso del tipo `any`

### Compilación y Pruebas
- [ ] `npm run build` se completa exitosamente
- [ ] dist/index.js creado y ejecutable
- [ ] Todas las importaciones se resuelven correctamente
