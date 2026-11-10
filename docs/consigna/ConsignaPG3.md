# Consigna PG3: Orquestación final, pruebas del prototipo y armado de carpeta

> **Fuente:** Cátedra de Inteligencia Artificial, UTN FRM, *Actividad PG3 – Unidad 4 (Grupal)*.
> **Ejemplo de referencia:** *Ejemplo_PG3_Evaluacion_CVs.docx* (entregado por la cátedra y resumido en la [sección 8](#8-ejemplo-de-la-cátedra-otro-dominio)). Trata otro problema, la evaluación de CV, así que sirve como guía de forma y no de contenido.
>
> Este archivo transcribe la consigna para tenerla en el repositorio. Si hay dudas, manda el PDF original.

---

## 1. Objetivo

Integrar los componentes desarrollados durante el proyecto en un **único asistente inteligente funcional**, capaz de:

- interpretar consultas,
- recuperar conocimiento,
- realizar inferencias,
- gestionar la incertidumbre,
- explicar sus conclusiones de manera comprensible para los usuarios.

La actividad busca validar el funcionamiento integral del sistema y documentar el proceso completo de construcción de la solución.

**En una línea:** el grupo consolida los flujos de PI4 en un único asistente, crea un punto de entrada común, ejecuta pruebas de integración de extremo a extremo y arma la carpeta final del proyecto.

### Contenidos de la materia que integra

Sistemas inteligentes · Ingeniería del conocimiento · Representación del conocimiento · Sistemas basados en reglas · Lógica difusa · Grafos de conocimiento · Procesamiento de lenguaje natural · Modelos de lenguaje · Asistentes inteligentes · Explicabilidad y trazabilidad.

### Lecturas recomendadas

- Todas las actividades previas del proyecto (PG0–PG2, PI1–PI4).
- Unidad 4: Implementación de modelos de inteligencia artificial.
- Arquitecturas de asistentes inteligentes.
- Explicabilidad y trazabilidad en sistemas basados en conocimiento.

---

## 2. Requisito central (lo que más se evalúa)

> El grupo debe **evitar que PG3 parezca una suma de scripts independientes**.

Tiene que existir:

- [ ] Un **System Prompt maestro** que enrute la consulta del usuario hacia el submódulo correspondiente.
- [ ] Una **API o interfaz unificada** (una sola entrada para el usuario).
- [ ] **Pruebas que demuestren que el sistema consulta múltiples submódulos.**

---

## 3. Actividades a realizar

### 3.1 Revisión y depuración final

Revisar de forma integral los componentes desarrollados durante el proyecto y verificar:

- [ ] coherencia conceptual,
- [ ] consistencia terminológica,
- [ ] funcionamiento de las consultas,
- [ ] funcionamiento de las reglas,
- [ ] funcionamiento de los componentes difusos,
- [ ] funcionamiento de la integración con el LLM.

- [ ] **Documentar las correcciones realizadas.**

### 3.2 Integración del asistente inteligente

Integrar los componentes en un único sistema. La solución debe incluir:

| Componente | Requisito |
| --- | --- |
| Base de conocimiento | Implementada en **Neo4j** |
| Mecanismos de razonamiento | Basados en reglas y en conocimiento explícito |
| Componentes difusos | Cuando correspondan |
| Modelo de lenguaje | Como interfaz de interacción y de explicación |
| Interfaz de usuario | Consola, aplicación web, API o interfaz equivalente |

### 3.3 Arquitectura final del sistema

Documentar la arquitectura completa. El diagrama debe mostrar:

- [ ] usuario,
- [ ] interfaz,
- [ ] modelo de lenguaje,
- [ ] componentes de orquestación,
- [ ] base de conocimiento,
- [ ] módulos de razonamiento,
- [ ] fuentes de información.

- [ ] **Explicar claramente la función de cada componente.**

### 3.4 Casos de uso integrados

Diseñar escenarios que involucren **varios submódulos**. Se recomienda incluir **al menos cinco** casos de uso integrales. Cada caso debe mostrar:

- [ ] situación planteada,
- [ ] información utilizada,
- [ ] razonamiento realizado,
- [ ] resultado obtenido,
- [ ] explicación generada.

### 3.5 Pruebas funcionales

Ejecutar pruebas que verifiquen:

- [ ] la recuperación de conocimiento,
- [ ] la ejecución de consultas,
- [ ] la activación de reglas,
- [ ] el funcionamiento de la lógica difusa,
- [ ] la generación de respuestas.

- [ ] **Documentar el resultado esperado y el obtenido.**

### 3.6 Evaluación del sistema

Analizar críticamente el comportamiento del asistente. Discutir:

- [ ] fortalezas,
- [ ] limitaciones,
- [ ] situaciones problemáticas,
- [ ] posibles errores,
- [ ] oportunidades de mejora.

### 3.7 Trazabilidad del conocimiento

Explicar cómo se puede rastrear el origen del conocimiento que usa el sistema. Identificar ejemplos donde se pueda reconstruir:

- [ ] la fuente del conocimiento,
- [ ] la regla utilizada,
- [ ] la evidencia considerada,
- [ ] la consulta ejecutada,
- [ ] la explicación generada.

**Objetivo:** demostrar que las conclusiones del sistema son justificables y auditables.

### 3.8 Reflexión sobre la metodología aplicada

Analizar brevemente cómo cada etapa del proyecto contribuyó a construir el sistema final:

- [ ] formulación del problema,
- [ ] análisis de las tareas expertas,
- [ ] adquisición de conocimiento,
- [ ] modelado conceptual,
- [ ] lógica difusa,
- [ ] implementación en grafos,
- [ ] integración con el LLM.

---

## 4. Formato del entregable

**Nombre del archivo:** `Grupo_N_PG3_ProyectoFinal.zip` (para nosotros: `Grupo_2_PG3_ProyectoFinal.zip`).

**Contenido mínimo:**

| | Ítem | Detalle |
| --- | --- | --- |
| **Documentación** | a) Informe ejecutivo final (PDF) | Resumen del problema, arquitectura final del sistema, manual de uso básico y conclusiones grupales |
| | b) Diagramas | |
| | c) Casos de prueba | |
| | d) Manual de uso | |
| **Implementación** | e) Código fuente | Carpeta con los scripts Python unificados y el archivo `requirements.txt` |
| | f) Scripts Cypher | |
| | g) Archivos de configuración | |
| | h) Recursos complementarios | |
| **Base de conocimiento** | i) Exportación de Neo4j | |
| | j) Datos de ejemplo | |
| **Material de presentación** | k) Video demostrativo o presentación multimedia | |
| | l) Infografía o resumen ejecutivo | |

---

## 5. Estructura sugerida del informe final

1. Portada institucional
2. Resumen ejecutivo
3. Descripción del problema
4. Arquitectura del sistema
5. Base de conocimiento
6. Integración con modelos de lenguaje
7. Casos de uso
8. Pruebas realizadas
9. Evaluación del sistema
10. Trazabilidad del conocimiento
11. Reflexiones finales
12. Referencias y fuentes consultadas

---

## 6. Resultado esperado

Al terminar, el grupo debe tener un **asistente inteligente completamente funcional** que integre:

- conocimiento explícito,
- razonamiento basado en reglas,
- representación de la incertidumbre,
- grafos de conocimiento,
- modelos de lenguaje,
- mecanismos de explicación.

El sistema debe poder responder consultas del dominio elegido (para nosotros, la selección de notebooks), justificar sus conclusiones y demostrar que integra de forma coherente los contenidos de toda la materia.

---

## 7. Criterios de evaluación

| Producto PG3 | Qué debe contener | Cómo se evalúa |
| --- | --- | --- |
| **Prompt maestro** | Instrucciones de enrutamiento y límites del asistente | Debe respetar que **Neo4j maneja la verdad** |
| **API o interfaz** | Entrada única para el usuario | Debe ejecutar los submódulos sin errores críticos |
| **Pruebas E2E** | Al menos **tres** casos complejos | Deben cruzar información de varios submódulos |
| **Informe ejecutivo** | Problema, arquitectura, uso y conclusiones | Debe ser coherente y profesional |
| **ZIP final** | Informe, código, `requirements.txt`, Cypher o dump, y video o infografía | Debe permitir revisar y reproducir el proyecto |

---

## 8. Ejemplo de la cátedra (otro dominio)

La cátedra compartió un ejemplo de entrega del **Grupo 1**, cuyo problema es la **evaluación de CV contra una vacante**. Es mucho más breve que lo que pide la consigna completa, pero muestra el nivel de detalle esperado en la arquitectura y en la traza de una prueba E2E.

### Qué contiene

**a) Objetivo.** Integrar un LLM para la extracción, Neo4j para las reglas y la lógica difusa, y otro LLM para la explicación, todo en una única aplicación (una API con FastAPI) que resuelve el problema planteado en PG0.

**b) Arquitectura final**, descrita como un flujo lineal:

1. El sistema expone un endpoint (`/evaluar_cv`) que recibe el texto del CV y el ID de la vacante.
2. Un LLM extrae los datos del texto en JSON (con LangChain).
3. Los datos extraídos se insertan en Neo4j.
4. Se ejecuta la consulta Cypher maestra de PG2, que cruza al candidato con la vacante.
5. El resultado de la consulta pasa a un LLM que redacta la explicación.
6. Se devuelve la explicación al usuario.

**c) Prueba E2E con su traza completa**, paso por paso:

| Paso | Qué se muestra |
| --- | --- |
| Entrada | Texto libre simulado y el ID de la vacante, con sus requisitos |
| JSON extraído | Los campos que sacó el LLM |
| Cypher | Faltantes excluyentes, grado difuso calculado (con la función y sus parámetros) y estado resultante |
| Prompt de explicación | Los datos exactos que recibió el LLM |
| Respuesta final | El texto que ve el usuario, que justifica el estado aunque un valor quede apenas por debajo del umbral (gracias a la lógica difusa) |

**d) Reflexión metodológica.** El LLM no decide; la lógica experta (incluida su flexibilidad difusa) vive en el grafo. El LLM es la interfaz lingüística.

### Qué tomar para nuestro proyecto

- **La traza E2E como formato de prueba:** entrada, JSON extraído, Cypher ejecutado con valores difusos, datos enviados al LLM y respuesta final. Cada prueba E2E nuestra debería documentarse así.
- **La idea central de la reflexión:** el LLM interpreta y explica, y Neo4j decide. Coincide con el criterio de evaluación del prompt maestro.

### En qué nos diferenciamos

- El ejemplo tiene **un solo flujo**. Nosotros tenemos **cuatro submódulos** (SM1–SM4), así que necesitamos lo que el ejemplo no muestra: el **prompt maestro con enrutamiento** y pruebas que crucen varios submódulos.
- El ejemplo **inserta** los datos del usuario en Neo4j. Si nosotros escribimos en el grafo o solo leemos se decide al definir la arquitectura.
- Nuestro dominio es la **selección de notebooks**: perfiles de uso, rendimiento, gráfica y movilidad, y costo-beneficio, en lugar de candidatos y vacantes.
