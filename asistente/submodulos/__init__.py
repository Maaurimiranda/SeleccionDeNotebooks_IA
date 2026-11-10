"""Submódulos del asistente. Cada uno es un paquete con la misma forma (ARQUITECTURA §2.1):

    __init__.py    exporta solo ejecutar()
    entrada.py     "controlador" del módulo: valida parámetros y despacha cada intención
    servicio.py    una función por intención: pide filas al repositorio y arma la evidencia
    repositorio.py CONSULTAS (Cypher fijo) y funciones que llaman a grafo.leer()
    esquemas.py    TypedDict de parámetros y evidencia

Un submódulo no importa a otro: solo a `comun` y a `asistente.contrato`.
"""
