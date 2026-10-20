"""
comparacion.py - Evitacion (banquero) frente a deteccion + recuperacion.

Se parte del mismo estado (ejemplo clasico despues de que P1 recibe (1, 0, 2))
y se aplica la misma solicitud de P0: (0, 2, 0).

  A) Con evitacion: el banquero simula, ve que el estado seria inseguro y
     posterga la solicitud. Luego, si cada proceso pide lo que le falta (su Need),
     la deteccion no encuentra interbloqueo.
  B) Sin evitacion: la solicitud se concede porque hay recursos libres. Luego
     cada proceso pide lo que le falta y queda esperando. El algoritmo de
     deteccion encuentra el interbloqueo y hay que recuperar abortando victimas.

Uso: python3 comparacion.py
"""
import copy

from banquero import restar, sumar, vec
from demo import ejemplo_clasico
from deteccion import detectar, recuperar


def linea(texto=""):
    print(texto)


def main():
    g = ejemplo_clasico()
    g.solicitar("P1", [1, 0, 2])
    req_p0 = [0, 2, 0]
    linea("Estado de partida (ejemplo clasico despues de conceder (1, 0, 2) a P1):")
    linea("\n".join(g.tabla_estado()))

    # ------------------------------------------------------- A) evitacion
    linea("\n" + "=" * 78)
    linea("A) CON EVITACION (algoritmo del banquero)")
    linea("=" * 78)
    ga = copy.deepcopy(g)
    r = ga.solicitar("P0", req_p0)
    linea(f"  P0 pide {vec(req_p0)} -> {r.estado}: el banquero vio en la simulacion que "
          f"Work = (2, 1, 0) no alcanza a nadie.")
    linea("  Despues, cada proceso pide lo que le falta (Request = Need). Deteccion:")
    det = detectar(ga.available, ga.allocation, ga.need, ga.procesos, ga.recursos)
    linea("\n".join(det.lineas))

    # ------------------------------------------------------ B) deteccion
    linea("\n" + "=" * 78)
    linea("B) SIN EVITACION (se asigna si hay recursos libres; se detecta despues)")
    linea("=" * 78)
    i = g.procesos.index("P0")
    av = restar(g.available, req_p0)
    al = copy.deepcopy(g.allocation)
    al[i] = sumar(al[i], req_p0)
    need = [restar(fm, fa) for fm, fa in zip(g.max, al)]
    linea(f"  P0 pide {vec(req_p0)} -> CONCEDIDA sin prueba de seguridad "
          f"(solo se miro que {vec(req_p0)} <= Available {vec(g.available)}).")
    linea(f"  Available queda en {vec(av)}.")
    linea("  Despues, cada proceso pide lo que le falta (Request = Need) y se queda esperando.")
    linea("  Deteccion (diapositiva 15):")
    det = detectar(av, al, need, g.procesos, g.recursos)
    linea("\n".join(det.lineas))

    linea("\n  Recuperacion por terminacion incremental (diapositiva 16):")
    _, lineas = recuperar(av, al, need, g.procesos, g.recursos)
    linea("\n".join(lineas))

    # ---------------------------------------------------------- resumen
    linea("\n" + "=" * 78)
    linea("RESUMEN")
    linea("=" * 78)
    linea("  Evitacion : P0 espera un poco; nadie pierde trabajo y nunca hay interbloqueo.")
    linea("              Costo: una prueba de seguridad O(m*n^2) en CADA solicitud.")
    linea("  Deteccion : la solicitud pasa al instante, pero el sistema se bloquea; hay que")
    linea("              detectar (O(m*n^2) cada vez que se ejecuta) y abortar una victima,")
    linea("              que pierde su trabajo y debe reiniciarse.")


if __name__ == "__main__":
    main()
