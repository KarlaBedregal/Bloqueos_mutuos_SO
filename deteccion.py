"""
deteccion.py - Algoritmo de deteccion de interbloqueo con multiples instancias
y recuperacion por terminacion incremental de victimas.

Sistemas Operativos - UNSA - 2026-B - Semana 8

A diferencia del banquero (evitacion), aqui los recursos ya se asignaron sin
preguntar. La deteccion usa la solicitud PENDIENTE actual (Request) en vez de
Need, y marca Finish[i] = T desde el inicio si el proceso no retiene nada
(Allocation[i] = 0), porque no puede formar parte del nucleo bloqueado.
"""
from __future__ import annotations

from dataclasses import dataclass

from banquero import formatear_traza, simular_finalizacion, sumar, texto_finish, vec


@dataclass
class ResultadoDeteccion:
    bloqueados: list           # indices con Finish = F al final
    simulacion: object         # ResultadoSimulacion
    lineas: list


def detectar(available, allocation, request, procesos, recursos) -> ResultadoDeteccion:
    finish0 = [not any(fila) for fila in allocation]   # Allocation[i] = 0 -> Finish = T
    res = simular_finalizacion(available, allocation, request, finish0)
    lineas = [f"  Finish inicial: T si Allocation = 0 -> {texto_finish(finish0)}"]
    lineas += ["  " + l for l in formatear_traza(res, available, allocation, request,
                                                 procesos, recursos, etiqueta="Request")]
    bloqueados = [i for i, f in enumerate(res.finish_final) if not f]
    if bloqueados:
        lineas.append("  RESULTADO: INTERBLOQUEO entre " +
                      ", ".join(procesos[i] for i in bloqueados) +
                      " (cada uno espera recursos retenidos por otro del mismo grupo)")
    else:
        lineas.append("  RESULTADO: no hay interbloqueo; orden posible de terminacion: <" +
                      ", ".join(procesos[i] for i in res.secuencia) + ">")
    return ResultadoDeteccion(bloqueados, res, lineas)


def recuperar(available, allocation, request, procesos, recursos) -> tuple:
    """Terminacion incremental: aborta una victima, repite la deteccion y sigue
    hasta romper el interbloqueo. Criterio de victima: la que, al liberar lo que
    retiene, deja terminar a mas procesos bloqueados; si empatan, la que retiene
    menos unidades (se pierde menos trabajo)."""
    av = list(available)
    al = [list(f) for f in allocation]
    rq = [list(f) for f in request]
    lineas, abortados = [], []
    while True:
        det = detectar(av, al, rq, procesos, recursos)
        if not det.bloqueados:
            lineas.append("  Tras la recuperacion ya no hay procesos bloqueados.")
            break
        mejor = None
        for v in det.bloqueados:
            av2 = sumar(av, al[v])
            al2 = [f if k != v else [0] * len(f) for k, f in enumerate(al)]
            rq2 = [f if k != v else [0] * len(f) for k, f in enumerate(rq)]
            fin = simular_finalizacion(av2, al2, rq2, [not any(f) for f in al2], registrar=False)
            liberados = sum(1 for k in det.bloqueados if k != v and fin.finish_final[k])
            clave = (liberados, -sum(al[v]))
            lineas.append(f"  Candidato {procesos[v]}: retiene {vec(al[v])}; si se aborta, "
                          f"pueden terminar {liberados} de los demas bloqueados")
            if mejor is None or clave > mejor[0]:
                mejor = (clave, v)
        v = mejor[1]
        lineas.append(f"  -> Victima elegida: {procesos[v]}. Se aborta y libera {vec(al[v])}: "
                      f"Available = {vec(av)} + {vec(al[v])} = {vec(sumar(av, al[v]))}")
        av = sumar(av, al[v])
        al[v] = [0] * len(al[v])
        rq[v] = [0] * len(rq[v])
        abortados.append(v)
    final = detectar(av, al, rq, procesos, recursos)
    lineas += final.lineas
    lineas.append("  Procesos abortados: " + ", ".join(procesos[k] for k in abortados) +
                  " (deben reiniciarse y perder su trabajo)")
    return abortados, lineas
