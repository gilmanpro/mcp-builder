# Guía de Evaluación de Servidores MCP

## Resumen

Este documento proporciona orientación sobre cómo crear evaluaciones completas para servidores MCP. Las evaluaciones prueban si los LLMs pueden usar efectivamente tu servidor MCP para responder preguntas realistas y complejas usando solo las herramientas proporcionadas.

---

## Referencia Rápida

### Requisitos de Evaluación
- Crea 10 preguntas legibles por humanos
- Las preguntas deben ser de SOLO LECTURA, INDEPENDIENTES, NO DESTRUCTIVAS
- Cada pregunta requiere múltiples llamadas a herramientas (potencialmente docenas)
- Las respuestas deben ser valores únicos y verificables
- Las respuestas deben ser ESTABLES (no cambiarán con el tiempo)

### Formato de Salida
```xml
<evaluation>
   <qa_pair>
      <question>Tu pregunta aquí</question>
      <answer>Respuesta única verificable</answer>
   </qa_pair>
</evaluation>
```

---

## Propósito de las Evaluaciones

La medida de calidad de un servidor MCP NO es qué tan bien o exhaustivamente implementa herramientas, sino qué tan bien estas implementaciones (esquemas de entrada/salida, docstrings/descripciones, funcionalidad) permiten a los LLMs sin otro contexto y con acceso SOLO a los servidores MCP responder preguntas realistas y difíciles.

## Descripción General de la Evaluación

Crea 10 preguntas legibles por humanos que requieran SOLO operaciones de SOLO LECTURA, INDEPENDIENTES, NO DESTRUCTIVAS e IDEMPOTENTES para responder. Cada pregunta debe ser:
- Realista
- Clara y concisa
- Inequívoca
- Compleja, requiriendo potencialmente docenas de llamadas a herramientas o pasos
- Respondible con un valor único y verificable que identifiques de antemano

## Guías para Crear Preguntas

### Requisitos Fundamentales

1. **Las preguntas DEBEN ser independientes**
   - Cada pregunta no debe depender de la respuesta de ninguna otra pregunta
   - No debe asumir operaciones de escritura previas de procesar otra pregunta

2. **Las preguntas DEBEN requerir SOLO uso de herramientas NO DESTRUCTIVAS e IDEMPOTENTES**
   - No deben instruir o requerir modificar el estado para llegar a la respuesta correcta

3. **Las preguntas deben ser REALISTAS, CLARAS, CONCISAS y COMPLEJAS**
   - Deben requerir que otro LLM use múltiples (potencialmente docenas de) herramientas o pasos para responder

### Complejidad y Profundidad

4. **Las preguntas deben requerir exploración profunda**
   - Considera preguntas multi-salto que requieran múltiples sub-preguntas y llamadas secuenciales a herramientas
   - Cada paso debe beneficiarse de la información encontrada en preguntas anteriores

5. **Las preguntas pueden requerir paginación extensa**
   - Pueden necesitar paginar a través de múltiples páginas de resultados
   - Pueden requerir consultar datos antiguos (1-2 años desactualizados) para encontrar información niche
   - Las preguntas deben ser DIFÍCILES

6. **Las preguntas deben requerir comprensión profunda**
   - En lugar de conocimiento superficial
   - Pueden plantear ideas complejas como preguntas de Verdadero/Falso que requieran evidencia
   - Pueden usar formato de opción múltiple donde el LLM debe buscar diferentes hipótesis

7. **Las preguntas no deben ser resolubles con búsqueda directa de palabras clave**
   - No incluyas palabras clave específicas del contenido objetivo
   - Usa sinónimos, conceptos relacionados o paráfrasis
   - Requiere múltiples búsquedas, analizar múltiples elementos relacionados, extraer contexto y luego derivar la respuesta

### Pruebas de Herramientas

8. **Las preguntas deben probar los valores de retorno de las herramientas**
   - Pueden provocar que las herramientas devuelvan grandes objetos JSON o listas, abrumando al LLM
   - Deben requerir entender múltiples modalidades de datos

9. **Las preguntas deben reflejar PRINCIPALMENTE casos de uso humano reales**

10. **Las preguntas pueden requerir docenas de llamadas a herramientas**

11. **Incluye preguntas ambiguas**
    - Pueden ser ambiguas O requerir decisiones difíciles sobre qué herramientas llamar

### Estabilidad

12. **Las preguntas deben diseñarse para que la respuesta NO CAMBIE**
    - No hagas preguntas que dependan del "estado actual" que es dinámico

13. **NO dejes que el servidor MCP RESTRINJA los tipos de preguntas que crees**

## Guías para Respuestas

### Verificación

1. **Las respuestas deben ser VERIFICABLES mediante comparación directa de cadenas**
   - Si la respuesta puede reescribirse en muchos formatos, especifica claramente el formato en la PREGUNTA
   - La respuesta debe ser un valor ÚNICO verificable

### Legibilidad

2. **Las respuestas deben preferir formatos LEGIBLES POR HUMANOS**
   - Nombres, primer nombre, apellido, fecha, nombre de archivo, URL, sí/no, verdadero/falso, a/b/c/d

### Estabilidad

3. **Las respuestas deben ser ESTABLES/ESTACIONARIAS**
   - Busca contenido antiguo (conversaciones que han terminado, proyectos lanzados)
   - Crea preguntas basadas en conceptos "cerrados"

### Diversidad

4. **Las respuestas deben ser DIVERSAS**
   - IDs de usuario, nombres, emails, teléfonos, IDs de canal, marcas de tiempo, etc.

5. **Las respuestas NO deben ser estructuras complejas**
   - No listas, objetos complejos, IDs múltiples o texto en lenguaje natural

## Proceso de Evaluación

### Paso 1: Inspección de Documentación
Lee la documentación de la API objetivo para entender endpoints disponibles, funcionalidad y requisitos de autenticación.

### Paso 2: Inspección de Herramientas
Lista las herramientas disponibles en el servidor MCP y comprende sus esquemas de entrada/salida y descripciones.

### Paso 3: Desarrollo de Comprensión
Repite los pasos 1 y 2 hasta que tengas un buen entendimiento de la API y las herramientas.

### Paso 4: Inspección de Contenido (Solo Lectura)
Usa las herramientas del servidor MCP para inspeccionar contenido usando SOLO operaciones de SOLO LECTURA.

### Paso 5: Generación de Tareas
Después de inspeccionar el contenido, crea 10 preguntas legibles por humanos.

## Formato de Salida

```xml
<evaluation>
   <qa_pair>
      <question>Encuentra el proyecto creado en Q2 2024 con el mayor número de tareas completadas. ¿Cuál es el nombre del proyecto?</question>
      <answer>Rediseño del Sitio Web</answer>
   </qa_pair>
   <qa_pair>
      <question>Busca issues etiquetados como "bug" que se cerraron en marzo 2024. ¿Qué usuario cerró la mayor cantidad? Proporciona su nombre de usuario.</question>
      <answer>sarah_dev</answer>
   </qa_pair>
</evaluation>
```

## Ejemplos de Preguntas

### Buenas Preguntas

**Ejemplo 1: Pregunta multi-salto (GitHub MCP)**
```xml
<qa_pair>
   <question>Encuentra el repositorio que fue archivado en Q3 2023 y que previamente había sido el proyecto más bifurcado en la organización. ¿Cuál era el lenguaje de programación principal usado en ese repositorio?</question>
   <answer>Python</answer>
</qa_pair>
```

**Ejemplo 2: Requiere comprensión contextual (MCP de Gestión de Proyectos)**
```xml
<qa_pair>
   <question>Localiza la iniciativa enfocada en mejorar la incorporación de clientes que se completó a finales de 2023. El líder del proyecto creó un documento retrospectivo después de completarlo. ¿Cuál era el título del rol del líder en ese momento?</question>
   <answer>Product Manager</answer>
</qa_pair>
```

**Ejemplo 3: Agregación compleja (MCP de Seguimiento de Issues)**
```xml
<qa_pair>
   <question>Entre todos los bugs reportados en enero 2024 marcados como criticidad alta, ¿qué asignado resolvió el mayor porcentaje de sus bugs asignados dentro de 48 horas? Proporciona el nombre de usuario del asignado.</question>
   <answer>alex_eng</answer>
</qa_pair>
```

### Malas Preguntas

**Ejemplo 1: Respuesta cambia con el tiempo**
```xml
<qa_pair>
   <question>¿Cuántos issues abiertos están actualmente asignados al equipo de ingeniería?</question>
   <answer>47</answer>
</qa_pair>
```

**Ejemplo 2: Demasiado fácil con búsqueda de palabras clave**
```xml
<qa_pair>
   <question>Encuentra el pull request con título "Agregar función de autenticación" y dime quién lo creó.</question>
   <answer>developer123</answer>
</qa_pair>
```

**Ejemplo 3: Formato de respuesta ambiguo**
```xml
<qa_pair>
   <question>Enumera todos los repositorios que tienen Python como su lenguaje principal.</question>
   <answer>repo1, repo2, repo3</answer>
</qa_pair>
```

## Proceso de Verificación

Después de crear las evaluaciones:
1. Examina el archivo XML para entender el esquema
2. Carga cada instrucción de tarea e intenta resolverla usando el servidor MCP
3. Identifica cualquier operación que requiera escritura u operaciones destructivas
4. Acumula todas las respuestas CORRECTAS y reemplaza respuestas incorrectas
5. Elimina cualquier `<qa_pair>` que requiera operaciones de escritura o destructivas

---

# Ejecución de Evaluaciones

Después de crear tu archivo de evaluación, puedes usar el harness de evaluación proporcionado para probar tu servidor MCP.

## Configuración

1. **Instalar Dependencias**
   ```bash
   pip install -r scripts/requirements.txt
   ```
   O manualmente:
   ```bash
   pip install anthropic mcp
   ```

2. **Configurar Clave de API**
   ```bash
   export ANTHROPIC_API_KEY=tu_clave_api
   ```

## Ejecución de Evaluaciones

El script de evaluación (`scripts/evaluation.py`) soporta tres tipos de transporte:

### 1. Servidor STDIO Local
```bash
python scripts/evaluation.py -t stdio -c python -a mi_servidor_mcp.py evaluation.xml
```

Con variables de entorno:
```bash
python scripts/evaluation.py -t stdio -c python -a mi_servidor.py -e API_KEY=abc123 evaluation.xml
```

### 2. SSE (Server-Sent Events)
```bash
python scripts/evaluation.py -t sse -u https://ejemplo.com/mcp evaluation.xml
```

### 3. HTTP (Streamable HTTP)
```bash
python scripts/evaluation.py -t http -u https://ejemplo.com/mcp evaluation.xml
```

## Opciones de Línea de Comandos

```
usage: evaluation.py [-h] [-t {stdio,sse,http}] [-m MODELO] [-c COMANDO]
                     [-a ARGS [ARGS ...]] [-e ENV [ENV ...]] [-u URL]
                     [-H HEADERS [HEADERS ...]] [-o SALIDA]
                     archivo_evaluacion
```

## Salida

El script de evaluación genera un reporte detallado incluyendo:
- Estadísticas de resumen (precisión, duración promedio, llamadas a herramientas)
- Resultados por tarea (correcto/incorrecto, duración, detalles)
- Comentarios del agente sobre las herramientas

### Guardar Reporte a un Archivo
```bash
python scripts/evaluation.py -t stdio -c python -a mi_servidor.py -o reporte_evaluacion.md evaluation.xml
```
