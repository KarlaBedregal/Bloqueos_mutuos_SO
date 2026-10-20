"""
demo.py - Casos de prueba del gestor de recursos explicados paso a paso.

Uso:
    python3 demo.py        (todos los casos)
    python3 demo.py 3      (solo el caso 3)

Caso 1: estado inicial seguro con su secuencia
Caso 2: solicitud valida y segura (se concede)
Caso 3: solicitud valida pero insegura (se posterga)
Caso 4: solicitud superior a Need (error)
Caso 5: solicitud superior a Available (el proceso espera)
Caso 6: datos invalidos sin alterar el estado
Caso 7: ejemplo de un solo tipo de recurso (diapositiva 13)
"""
import sys

from banquero import DatosInvalidos, GestorRecursos


def ejemplo_clasico() -> GestorRecursos:
    """Ejemplo de Silberschatz: 5 procesos y 3 tipos de recurso (A=10, B=5, C=7)."""
    return GestorRecursos(
        max_=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
        allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
        total=[10, 5, 7])


def ejemplo_un_recurso() -> GestorRecursos:
    """Ejemplo de la diapositiva 13: Total = 10, Asignacion 3,2,2 y Maximo 5,4,7."""
    return GestorRecursos(max_=[[5], [4], [7]], allocation=[[3], [2], [2]], total=[10],
                          recursos=["R"], procesos=["P1", "P2", "P3"])


def titulo(num, texto):
    print("\n" + "=" * 78)
    print(f"CASO {num}: {texto}")
    print("=" * 78)


def sin_cambios(g, antes, despues=None):
    despues = despues or g.instantanea()
    print(f"  Estado igual antes y despues: {'SI' if antes == despues else 'NO'}")


def caso1():
    titulo(1, "estado inicial seguro con secuencia")
    g = ejemplo_clasico()
    print(g.evaluar_estado())


def caso2():
    titulo(2, "solicitud valida y segura -> se concede")
    g = ejemplo_clasico()
    print(g.solicitar("P1", [1, 0, 2]))
    print("\n  Estado despues de conceder:")
    print("\n".join(g.tabla_estado()))


def caso3():
    titulo(3, "solicitud valida pero insegura -> se posterga")
    g = ejemplo_clasico()
    r = g.solicitar("P1", [1, 0, 2])
    print(f"  (Se parte del estado del caso 2: P1 recibio (1, 0, 2) -> {r.estado}, "
          f"Available = (2, 3, 0))\n")
    antes = g.instantanea()
    print(g.solicitar("P0", [0, 2, 0]))
    sin_cambios(g, antes)


def caso4():
    titulo(4, "solicitud superior a Need -> error")
    g = ejemplo_clasico()
    antes = g.instantanea()
    print(g.solicitar("P1", [2, 0, 0]))
    sin_cambios(g, antes)


def caso5():
    titulo(5, "solicitud superior a Available -> el proceso espera")
    g = ejemplo_clasico()
    antes = g.instantanea()
    print(g.solicitar("P0", [4, 0, 0]))
    sin_cambios(g, antes)


def caso6():
    titulo(6, "datos invalidos sin alterar el estado")
    g = ejemplo_clasico()
    antes = g.instantanea()
    pruebas = [("P7", [1, 0, 0], "proceso inexistente"),
               ("P1", [1, 0], "falta un componente"),
               ("P1", [1, -1, 0], "valor negativo"),
               ("P1", [1, "x", 0], "valor que no es entero"),
               ("P1", [0, 0, 0], "solicitud vacia")]
    for proc, req, desc in pruebas:
        print(f"\n  -- {desc} --")
        print(g.solicitar(proc, req))
    print("\n  -- liberar mas de lo asignado --")
    print(g.liberar("P3", [3, 0, 0]))
    print()
    sin_cambios(g, antes)

    print("\n  -- datos iniciales invalidos (el gestor no se crea) --")
    iniciales = [
        ("Allocation > Max", dict(max_=[[2, 2], [1, 1]], allocation=[[3, 0], [0, 0]],
                                  available=[1, 1])),
        ("asignado mayor que el total", dict(max_=[[4], [4]], allocation=[[3], [3]],
                                             total=[5])),
        ("filas de distinto tamano", dict(max_=[[2, 2], [1]], allocation=[[1, 1], [1]],
                                          available=[1, 1])),
        ("Available negativo", dict(max_=[[2]], allocation=[[1]], available=[-1])),
    ]
    for desc, datos in iniciales:
        try:
            GestorRecursos(**datos)
            print(f"  {desc}: se creo (no deberia)")
        except DatosInvalidos as e:
            print(f"  {desc}: RECHAZADO -> {e}")


def caso7():
    titulo(7, "un solo tipo de recurso (ejemplo de la diapositiva 13)")
    g = ejemplo_un_recurso()
    print(g.evaluar_estado())
    print("\n  Ejercicio rapido: P3 solicita 3 unidades cuando Available = 3")
    antes = g.instantanea()
    print(g.solicitar("P3", [3]))
    sin_cambios(g, antes)


CASOS = {1: caso1, 2: caso2, 3: caso3, 4: caso4, 5: caso5, 6: caso6, 7: caso7}

if __name__ == "__main__":
    elegidos = [int(a) for a in sys.argv[1:]] or list(CASOS)
    for c in elegidos:
        CASOS[c]()
