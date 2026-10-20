# Gestor de recursos seguro – Algoritmo del banquero (Python)

Sistemas Operativos · UNSA · 2026-B · Semana 8: Bloqueos mutuos
Docente: MSc. Norman Patrick Harvey Arce · Alumna: Bedregal Coaguila, Karla Miluska

Gestor con N procesos y M tipos de recurso. Recibe **Max**, **Allocation** y
**Available** (o el total), calcula **Need**, valida cada solicitud, la simula en
una copia y solo la concede si existe una secuencia segura. Cada decisión se
explica paso a paso (Available, Work y Finish). Los datos inválidos se rechazan
sin alterar el estado. Incluye también el algoritmo de detección con
recuperación para comparar evitación y detección.

Solo usa la biblioteca estándar de Python 3 (3.10 o superior).

| Archivo | Contenido |
|---|---|
| `banquero.py` | Núcleo: gestor, prueba de seguridad, solicitudes, liberaciones y modo consola |
| `deteccion.py` | Detección de interbloqueo (múltiples instancias) y recuperación por víctimas |
| `demo.py` | Casos 1 a 7 explicados paso a paso |
| `comparacion.py` | Evitación frente a detección sobre la misma solicitud |
| `complejidad.py` | Medición del costo de la prueba de seguridad (mejor y peor caso) |
| `test_banquero.py` | 13 pruebas automatizadas (`unittest`) |
| `estado_ejemplo.json` | Estado inicial del ejemplo clásico (5 procesos, 3 recursos) |
| `estado_invalido.json` | Estado con Allocation > Max, para probar el rechazo |
| `solicitudes_ejemplo.txt` | Solicitudes dinámicas para el modo consola |

## Ejecución

```bash
python3 demo.py                 # todos los casos (o: python3 demo.py 3)
python3 comparacion.py          # evitación vs detección
python3 complejidad.py          # análisis de complejidad
python3 -m unittest -v test_banquero

python3 banquero.py estado_ejemplo.json                          # solicitudes interactivas
python3 banquero.py estado_ejemplo.json solicitudes_ejemplo.txt  # solicitudes desde archivo
python3 banquero.py estado_invalido.json                         # datos iniciales inválidos
```

Comandos del modo consola: `estado`, `seguro`, `solicitar P1 1 0 2`,
`liberar P1 1 0 0`, `ayuda`, `salir`.
