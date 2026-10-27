# Seguridad de servidores MCP

MCP **no incorpora autenticación, autorización ni cifrado nativos** (Cloudflare): corre sobre HTTP en muchas implementaciones y todo ese control lo añades tú. Este documento es la norma de seguridad de la skill: léelo antes de entregar cualquier servidor y al auditar uno existente.

## Índice

1. Seis vectores de ataque reales
2. Requisitos obligatorios (especificación MCP 2026-07-28)
3. Autenticación y tokens
4. Validación de entrada y ejecución de herramientas
5. Secretos
6. Red y transporte
7. Registro y monitorización
8. Defensas específicas de IA
9. Cadena de suministro y despliegue
10. Checklist final de entrega
11. Fuentes

---

## 1. Seis vectores de ataque reales

Datos de auditorías masivas del ecosistema (Docker/arXiv, Backslash, CVEs públicos):

| # | Vector | Dato | Mitigación concreta |
|---|--------|------|---------------------|
| 1 | **OAuth/frágil descubrimiento**: endpoints de autorización que inyectan comandos (p. ej. CVE-2025-6514 en `mcp-remote`, +500 000 descargas) | 43% de servidores con inyección de comandos | OAuth 2.1 propio y nativo; no usar proxies OAuth de terceros que ejecuten shell; solo endpoints `https` |
| 2 | **Inyección de comandos**: construcción de comandos con datos de usuario, ejecución dinámica de código sin validar | decenas de casos públicos | Nunca montar comandos con entradas del LLM; listas de permitido; entradas por esquema estricto |
| 3 | **Acceso de red sin restricciones**: fetch de URLs arbitrarias, C2, exfiltración | 33% permiten URL fetch sin límite | Lista blanca de destinos; justificar cada dominio contactado; monitorizar conexiones salientes |
| 4 | **Exposición de sistema de archivos**: paths fuera del directorio previsto | 22% con fuga de archivos | Resolución canónica de paths + raíz permitida (`Path.resolve()` dentro de la raíz, si no, error); no dar acceso más allá de la carpeta de trabajo |
| 5 | **Tool poisoning**: descripciones o respuestas falsas que manipulan al agente | 5.5% con ataques específicos MCP | Revisar descripciones antes de instalar; auditoría de cambios de metadata; logs completos de llamadas |
| 6 | **Fuga de secretos**: claves en variables de entorno planas, listas de procesos y logs | 66% con malas prácticas de código | Gestor de secretos o env var sin imprimir; jamás en respuestas ni logs |

---

## 2. Requisitos obligatorios (especificación MCP 2026-07-28)

1. **Validación de tokens**: NO aceptar ningún token que no haya sido emitido explícitamente para este servidor (validar `aud`).
2. **Verificación de autorización**: verificar TODAS las solicitudes entrantes; NO usar la sesión como autenticación.
3. **Consentimiento del usuario**: los proxies con IDs de cliente de terceros deben pedir consentimiento explícito antes de reenviar flujos de autorización.
4. **Estado de aplicación**: la posesión de un identificador de estado NO es autenticación; autorizar cada solicitud que lo use. Manejadores opacos, no deterministas, vinculados al principal autenticado, con expiración y revocación.

---

## 3. Autenticación y tokens

- **OAuth 2.1** con proveedor de identidad externo establecido (Entra ID, Auth0, Cloudflare Access…) en vez de autenticación casera. Validar certificados y la audiencia del token contra este servidor.
- **Tokens de corta duración** con rotación segura; **MFA** para accesos administrativos y operaciones sensibles.
- **Permisos granulares por herramienta**, principio de menor privilegio: exponer una herramienta no debe eludir ni debilitar los controles de autorización de la API subyacente.
- **Prohibido el paso de token** (token passthrough) entre clientes y otros servicios.
- **Registro de cliente**: preferir metadatos de ID de cliente o pre-registro; el registro dinámico de cliente está obsoleto.
- Servidor local sin exposición remota: enlazar a `127.0.0.1` y validar el encabezado `Origin` en cada conexión (defensa DNS rebinding).

## 4. Validación de entrada y ejecución de herramientas

- Esquema estricto en TODA entrada (Pydantic/Zod `.strict()`): tipos, longitudes, rangos, enums; rechazar campos extra.
- Sanear rutas de archivo y URLs; verificar pertenencia a la raíz permitida tras resolver la ruta canónica.
- Nunca construir comandos de sistema con datos del usuario ni evaluar código recibido; si una herramienta necesita ejecutar procesos, usa argumentos en lista fijos y predefinidos.
- Verificar tamaños y rangos; rate limiting multinivel (por usuario, credencial, herramienta y operación) y cuotas de CPU/memoria/tiempo.
- Ejecución en entornos aislados (contenedores, sin privilegios elevados, red segmentada) cuando el servidor procese entradas no confiables.

## 5. Secretos

- Credenciales en **gestor de secretos dedicado** (Key Vault, secretos de Docker Desktop, `op`, etc.) o, como mínimo, variables de entorno leídas una vez y nunca impresas.
- Jamás en: código fuente, `.env` commiteado, logs, mensajes de error devueltos al cliente, respuestas de herramientas ni URLs de conexión.
- Rotación de claves y segregación por entorno (dev/prod distintos). Escanear respuestas de herramientas ante fugas posibles.

## 6. Red y transporte

- **HTTPS con validación de certificados** obligatorio en cualquier HTTP remoto; sin TLS no hay protección on-path.
- Servidor local: `127.0.0.1`, validación de `Origin`, sin puertos abiertos en la LAN.
- Lista blanca de destinos salientes; justificar en la documentación cada dominio que el servidor contacta.
- stdio: aislamiento de procesos y credenciales por entorno; **logs en stderr, jamás en stdout** (stdout es el canal del protocolo).

## 7. Registro y monitorización

- Registro estructurado y auditable de cada invocación: herramienta, argumentos (sin secretos), principal, resultado, duración.
- Correlación con respuesta a incidentes: alertas por patrones anómalos (herramienta nunca usada de pronto en ráfaga, errores 403/429 masivos).
- Registrar eventos de seguridad respetando privacidad: sin PII innecesaria ni secretos en claro.

## 8. Defensas específicas de IA

- **Tool poisoning**: no confíes en descripciones de servidores no verificados; monitoriza cambios de metadata entre sesiones; los cambios de descripción/esquema/permisos son cambios de API y se versionan.
- **Inyección de prompt**: los datos que devuelve una herramienta son dato, no instrucción; delimita y marca datos externos en las respuestas para que el modelo no los obedezca como órdenes.
- **Salida del modelo/servidor**: sanea lo que se devuelve a interfaces web (XSS) y evita que datos sensibles caigan en instrucciones.
- **Ventana de contexto**: limita el tamaño de las respuestas (truncamiento con aviso y sugerencia de paginación) para evitar envenenamiento de contexto.
- **Consentimiento**: el usuario debe ver y aceptar acciones y accesos a datos; herramientas destructivas con confirmación explícita.

## 9. Cadena de suministro y despliegue

- Instalar solo paquetes de registros oficiales, con versión fijada y revisión previa del código del servidor (lee el código antes de ejecutarlo).
- Inventario de dependencias y escaneo de vulnerabilidades en CI/CD; revisiones de seguridad obligatorias para cambios MCP.
- Preferir imágenes firmadas criptográficamente y aislamiento por contenedor con límites de CPU/memoria.
- Tratar el servidor como **infraestructura compartida**: contratos claros, pruebas, versionado y gobernanza de cambios (ver `mcp_best_practices.md`).

## 10. Checklist final de entrega

- [ ] Credenciales fuera del código y fuera de logs/respuestas.
- [ ] Esquema estricto en todas las herramientas; paths canónicos; sin construcción de comandos con entradas.
- [ ] HTTP: TLS + OAuth 2.1 con `aud` + `Origin` + rate limiting. Local: `127.0.0.1`.
- [ ] Lista blanca de red; logs en stderr/archivo sin secretos; auditoría de invocaciones.
- [ ] Anotaciones puestas; destructivas separadas y con confirmación.
- [ ] Dependencias fijadas y auditadas; servidor aislado con mínimo privilegio.
- [ ] Respuestas truncadas/paginadas; errores accionables sin filtrar internals.

## 11. Fuentes

- Microsoft mcp-for-beginners, "Mejores prácticas de seguridad MCP" (spec 2026-07-28): github.com/microsoft/mcp-for-beginners (translations/es/02-Security)
- Docker, "MCP Horror Stories: security issues threatening AI infrastructure" (2025): docker.com/blog/mcp-security-issues-threatening-ai-infrastructure
- Cloudflare Learning, "¿Qué es MCP?": cloudflare.com/es-es/learning/ai/what-is-model-context-protocol-mcp
- Google Cloud, "¿Qué es el Protocolo de contexto del modelo?": cloud.google.com/discover/what-is-model-context-protocol
