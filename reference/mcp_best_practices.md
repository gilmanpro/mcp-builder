# Mejores Prácticas para Servidores MCP

## ¿MCP o API directa? (decisión antes de escribir código)

MCP no sustituye a las APIs: las consume mediante una interfaz estándar de descubrimiento. Empieza por el problema de integración, no por el protocolo.

**La API directa basta cuando:**
- Pocos agentes con flujos estrictamente definidos y estables.
- Las capacidades no se comparten entre agentes ni aplicaciones.
- Un solo equipo es propietario de los agentes y sus integraciones.

**MCP se vuelve valioso cuando:**
- Muchos agentes/equipos necesitan las mismas capacidades.
- Las mismas integraciones se están duplicando.
- Necesitas descubrimiento y acceso estándar a herramientas, o estás construyendo orquestación multiagente.
- La complejidad de integración crece con cada agente nuevo.

Piensa en un espectro, no en una binaria: empieza por las capacidades donde la normalización, reutilización y gobernanza compartida aportan valor claro.

### Capacidades que merecen la pena compartir
Candidatos fuertes: buscar registros de clientes, verificar inventario, crear casos de soporte, consultar datos financieros, buscar conocimiento interno. Deben ser de uso general, relativamente estables y reutilizables en múltiples agentes.

### Diseña para agentes, no para APIs
No expongas docenas de endpoints de nivel bajo. Proporciona herramientas de negocio que el agente pueda descubrir, entender, combinar y usar con fiabilidad:
- `search_customer`, `get_open_orders`, `create_support_case`
- no `execute_function_7`, ni `POST /v2/customers?fields=...`

---

## Referencia Rápida

### Nombres de Servidores
- **Python**: `{servicio}_mcp` (ej., `slack_mcp`)
- **Node/TypeScript**: `{servicio}-mcp-server` (ej., `slack-mcp-server`)

### Nombres de Herramientas
- Usa snake_case con prefijo del servicio
- Formato: `{servicio}_{acción}_{recurso}`
- Ejemplo: `slack_send_message`, `github_create_issue`

### Formatos de Respuesta
- Soporta formatos JSON y Markdown
- JSON para procesamiento programático
- Markdown para legibilidad humana

### Paginación
- Respeta siempre el parámetro `limit`
- Devuelve `has_more`, `next_offset`, `total_count`
- Valor predeterminado de 20-50 elementos

### Transporte
- **Streamable HTTP**: Para servidores remotos, escenarios multi-cliente
- **stdio**: Para integraciones locales, herramientas de línea de comandos
- Evita SSE (obsoleto en favor de Streamable HTTP)

---

## Convenciones de Nombres de Servidores

Sigue estos patrones de nomenclatura estandarizados:

**Python**: Usa el formato `{servicio}_mcp` (minúsculas con guiones bajos)
- Ejemplos: `slack_mcp`, `github_mcp`, `jira_mcp`

**Node/TypeScript**: Usa el formato `{servicio}-mcp-server` (minúsculas con guiones)
- Ejemplos: `slack-mcp-server`, `github-mcp-server`, `jira-mcp-server`

El nombre debe ser general, descriptivo del servicio que se integra, fácil de inferir de la descripción de la tarea y sin números de versión.

---

## Nombres y Diseño de Herramientas

### Nombres de Herramientas

1. **Usa snake_case**: `search_users`, `create_project`, `get_channel_info`
2. **Incluye prefijo del servicio**: Anticipa que tu servidor MCP puede usarse junto con otros servidores MCP
   - Usa `slack_send_message` en lugar de solo `send_message`
   - Usa `github_create_issue` en lugar de solo `create_issue`
3. **Sé orientado a la acción**: Comienza con verbos (get, list, search, create, etc.)
4. **Sé específico**: Evita nombres genéricos que podrían entrar en conflicto con otros servidores

### Diseño de Herramientas

- Las descripciones de las herramientas deben describir la funcionalidad de manera estrecha e inequívoca
- Las descripciones deben coincidir precisamente con la funcionalidad real
- Proporciona anotaciones de herramientas (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
- Mantén las operaciones de las herramientas enfocadas y atómicas

---

## Formatos de Respuesta

Todas las herramientas que devuelvan datos deben soportar múltiples formatos:

### Formato JSON (`response_format="json"`)
- Datos estructurados legibles por máquina
- Incluye todos los campos disponibles y metadatos
- Nombres y tipos de campo consistentes
- Úsalo para procesamiento programático

### Formato Markdown (`response_format="markdown"`, típicamente predeterminado)
- Texto formateado legible por humanos
- Usa encabezados, listas y formato para claridad
- Convierte marcas de tiempo a formato legible por humanos
- Muestra nombres para mostrar con IDs entre paréntesis
- Omite metadatos verbosos

---

## Paginación

Para herramientas que listan recursos:

- **Respeta siempre el parámetro `limit`**
- **Implementa paginación**: Usa `offset` o paginación basada en cursor
- **Devuelve metadatos de paginación**: Incluye `has_more`, `next_offset`/`next_cursor`, `total_count`
- **Nunca cargues todos los resultados en memoria**: Especialmente importante para conjuntos de datos grandes
- **Valores predeterminados razonables**: 20-50 elementos es típico

Ejemplo de respuesta de paginación:
```json
{
  "total": 150,
  "count": 20,
  "offset": 0,
  "items": [...],
  "has_more": true,
  "next_offset": 20
}
```

---

## Opciones de Transporte

### Streamable HTTP

**Mejor para**: Servidores remotos, servicios web, escenarios multi-cliente

**Características**:
- Comunicación bidireccional sobre HTTP
- Soporta múltiples clientes simultáneos
- Puede desplegarse como un servicio web
- Habilita notificaciones del servidor al cliente

**Usa cuando**:
- Sirvas a múltiples clientes simultáneamente
- Despliegues como un servicio en la nube
- Integración con aplicaciones web

### stdio

**Mejor para**: Integraciones locales, herramientas de línea de comandos

**Características**:
- Comunicación por flujo de entrada/salida estándar
- Configuración simple, no necesita configuración de red
- Se ejecuta como un subproceso del cliente

**Usa cuando**:
- Construyas herramientas para entornos de desarrollo locales
- Integración con aplicaciones de escritorio
- Escenarios de un solo usuario y una sola sesión

**Nota**: Los servidores stdio NO deben registrar en stdout (usa stderr para registro)

### Selección de Transporte

| Criterio | stdio | Streamable HTTP |
|----------|-------|-----------------|
| **Despliegue** | Local | Remoto |
| **Clientes** | Único | Múltiples |
| **Complejidad** | Baja | Media |
| **Tiempo real** | No | Sí |

---

## El servidor como infraestructura compartida

Un servidor que empieza sirviendo a un agente acaba siendo dependencia de varios equipos: un cambio en nombre, esquema, permiso o comportamiento de una herramienta afecta a todos los consumidores. Gobiérnalo como una API pública:

- **Contratos claros**: descripciones que describan la funcionalidad de forma estrecha e inequívoca y coincidan exactamente con lo que hace la herramienta.
- **Gestión del cambio**: los cambios en nombres, descripciones, esquemas o permisos de herramientas son cambios de API; versiona, documenta y avisa. Pueden cambiar cómo los agentes seleccionan e invocan herramientas.
- **Límites entre lectura y escritura**: separa explícitamente operaciones que leen de las que crean/modifican/destruyen; las destructivas llevan interfaz y controles apropiados.
- **Observabilidad**: monitoriza fallos de herramienta, latencia, fallos de dependencias y patrones de uso inusuales; una herramienta poco fiable se propaga a todos los agentes.
- **Pruebas rigurosas**: no solo "¿funciona?", sino "¿el agente elige la herramienta correcta, pasa entradas válidas, interpreta la salida y respeta autorización?"; incluye casos de fallo y casos límite.
- **Permisos**: acceso con privilegio mínimo; exponer vía MCP no debe eludir los controles de autorización del sistema subyacente.

## Buenas prácticas de despliegue

- **Un propósito por servidor**: agrupa por dominio (`github_mcp`, `jira_mcp`), no un servidor-monolito con 50 herramientas de dominios distintos.
- **Configuración como código**: transporte, puerto, raíces y listas de permitido en fichero versionado; credenciales NUNCA en él.
- **Versionado**: `version` semver en el servidor; registra breaking changes de herramientas.
- **Aislamiento**: contenedor con límites de CPU/memoria y mínimo privilegio cuando procese entradas no confiables; local siempre en `127.0.0.1`.
- **Verificación previa**: lee el código de cualquier servidor de terceros antes de instalarlo; solo registros oficiales con versión fijada.
- **Evaluación en CI**: ejecuta un set de evaluaciones (ver `evaluation.md`) para detectar regresiones de utilidad además de errores.

---

## Mejores Prácticas de Seguridad

> La norma canónica de seguridad (6 vectores de ataque, requisitos MUST, checklist de entrega) vive en `seguridad.md`; esta sección es el resumen de diseño.

### Autenticación y Autorización

**OAuth 2.1**:
- Usa OAuth 2.1 seguro con certificados de autoridades reconocidas
- Valida los tokens de acceso antes de procesar solicitudes
- Solo acepta tokens destinados específicamente a tu servidor

**Claves de API**:
- Almacena las claves de API en variables de entorno, nunca en el código
- Valida las claves al iniciar el servidor
- Proporciona mensajes de error claros cuando la autenticación falla

### Validación de Entrada

- Sanitiza las rutas de archivos para prevenir directory traversal
- Valida URLs e identificadores externos
- Verifica tamaños y rangos de parámetros
- Previene inyección de comandos en llamadas del sistema
- Usa validación de esquemas (Pydantic/Zod) para todas las entradas

### Manejo de Errores

- No expongas errores internos a los clientes
- Registra errores relevantes para la seguridad en el servidor
- Proporciona mensajes de error útiles pero no reveladores
- Limpia los recursos después de errores

### Protección contra DNS Rebinding

Para servidores Streamable HTTP que se ejecutan localmente:
- Habilita la protección contra DNS rebinding
- Valida el encabezado `Origin` en todas las conexiones entrantes
- Vincula a `127.0.0.1` en lugar de `0.0.0.0`

---

## Anotaciones de Herramientas

Proporciona anotaciones para ayudar a los clientes a entender el comportamiento de las herramientas:

| Anotación | Tipo | Predeterminado | Descripción |
|-----------|------|----------------|-------------|
| `readOnlyHint` | boolean | false | La herramienta no modifica su entorno |
| `destructiveHint` | boolean | true | La herramienta puede realizar actualizaciones destructivas |
| `idempotentHint` | boolean | false | Llamadas repetidas con los mismos args no tienen efecto adicional |
| `openWorldHint` | boolean | true | La herramienta interactúa con entidades externas |

**Importante**: Las anotaciones son sugerencias, no garantías de seguridad. Los clientes no deben tomar decisiones críticas de seguridad basándose únicamente en las anotaciones.

---

## Manejo de Errores

- Usa códigos de error JSON-RPC estándar
- Reporta errores de herramientas dentro de objetos de resultado (no errores a nivel de protocolo)
- Proporciona mensajes de error útiles y específicos con próximos pasos sugeridos
- No expongas detalles de implementación interna
- Limpia los recursos adecuadamente en caso de errores

Ejemplo de manejo de errores:
```typescript
try {
  const result = performOperation();
  return { content: [{ type: "text", text: result }] };
} catch (error) {
  return {
    isError: true,
    content: [{
      type: "text",
      text: `Error: ${error.message}. Try using filter='active_only' to reduce results.`
    }]
  };
}
```

---

## Requisitos de Pruebas

Las pruebas exhaustivas deben cubrir:

- **Pruebas funcionales**: Verifica la ejecución correcta con entradas válidas/inválidas
- **Pruebas de integración**: Prueba la interacción con sistemas externos
- **Pruebas de seguridad**: Valida autenticación, sanitización de entrada, limitación de tasa
- **Pruebas de rendimiento**: Verifica el comportamiento bajo carga, tiempos de espera
- **Manejo de errores**: Asegura un reporte y limpieza adecuados de errores

---

## Requisitos de Documentación

- Proporciona documentación clara de todas las herramientas y capacidades
- Incluye ejemplos funcionales (al menos 3 por característica principal)
- Documenta las consideraciones de seguridad
- Especifica los permisos y niveles de acceso requeridos
- Documenta los límites de tasa y características de rendimiento
