# 3. Descripción del problema

Elegir una notebook es una decisión con muchas variables técnicas (CPU, RAM y su ampliabilidad, GPU, pantalla, peso, autonomía) que el comprador no sabe traducir a partir de lo que necesita. Un comprador dice «la uso para programar y virtualizar, y a veces juego» y «tengo 1000 USD»; un **asesor** de venta tiene que convertir eso en requisitos y compararlos contra un catálogo cuyas fichas suelen estar incompletas: muchas no informan si la RAM es ampliable, si la CPU soporta virtualización o cuánto dura la batería en uso real.

**Usuario y beneficiario.** El sistema lo usa el asesor; el beneficiario es el comprador. La explicación se escribe para el asesor, que la transmite.

**Por qué hace falta un experto.** La tarea combina conocimiento técnico (qué exige cada perfil de uso, qué riesgo implica quedarse corto de RAM), criterio para la incertidumbre («a veces», «liviana», un dato faltante) y políticas de decisión (un requisito excluyente no se compensa con puntaje). Un técnico lo resuelve por experiencia; el sistema lo hace explícito en reglas crisp, lógica difusa Mamdani y un grafo de conocimiento en Neo4j, con una traza de cada conclusión.

**Alcance del prototipo.**
- Recomienda hasta tres notebooks según el uso y el presupuesto, con alertas y una explicación trazable.
- Interpreta pedidos cargados (`req_01`, `req_02`, `req_03`) sobre un catálogo de prueba de 9 modelos con precios al 01/10/2026.
- Conserva la incertidumbre: un dato faltante se informa como rango o como «falta verificar», nunca se completa en silencio.
- **Fuera de alcance:** decidir la compra, precios en tiempo real, medir componentes, teclado, sonido y construcción, y procesadores ARM. El LLM interpreta la consulta y redacta; no decide ni calcula.
