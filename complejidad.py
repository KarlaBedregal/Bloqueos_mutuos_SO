"""
complejidad.py - Medicion del costo de la prueba de seguridad.

Peor caso: cada pasada solo puede terminar el ULTIMO proceso pendiente, asi que
la busqueda recorre todos los pendientes en cada paso:
    evaluaciones = n + (n-1) + ... + 1 = n(n+1)/2   -> O(n^2) comparaciones de
    vectores, cada una de m elementos               -> O(m * n^2)
Mejor caso: siempre puede terminar el primer pendiente -> n evaluaciones.

Uso: python3 complejidad.py
"""
import csv
import os
import time

from banquero import algoritmo_seguridad


def peor_caso(n, m):
    # Need[i] = n - i en cada recurso; Allocation[i] = 1; Available = 1.
    # Solo P(n-1) puede terminar al inicio, luego P(n-2), y asi sucesivamente.
    need = [[n - i] * m for i in range(n)]
    allocation = [[1] * m for _ in range(n)]
    return [1] * m, allocation, need


def mejor_caso(n, m):
    # Need[i] = 0: el primer pendiente siempre puede terminar.
    return [1] * m, [[1] * m for _ in range(n)], [[0] * m for _ in range(n)]


def medir(generador, n, m, reps=5):
    available, allocation, need = generador(n, m)
    tiempos = []
    for _ in range(reps):
        t0 = time.perf_counter()
        res = algoritmo_seguridad(available, allocation, need, registrar=False)
        tiempos.append((time.perf_counter() - t0) * 1000)
    assert res.completo
    return res.evaluaciones, sum(tiempos) / reps


def main():
    m = 3
    filas = []
    print(f"Prueba de seguridad con m = {m} tipos de recurso (promedio de 5 ejecuciones)\n")
    print(f"{'caso':<6} {'n':>5} {'evaluaciones':>13} {'n(n+1)/2':>10} {'tiempo (ms)':>12}"
          f" {'t / n^2 (us)':>13}")
    for nombre, gen in (("mejor", mejor_caso), ("peor", peor_caso)):
        for n in (50, 100, 200, 400, 800):
            ev, t = medir(gen, n, m)
            filas.append((nombre, n, m, ev, t))
            print(f"{nombre:<6} {n:>5} {ev:>13} {n * (n + 1) // 2:>10} {t:>12.3f}"
                  f" {t * 1000 / n ** 2:>13.4f}")
    os.makedirs("resultados", exist_ok=True)
    with open("resultados/complejidad.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["caso", "n", "m", "evaluaciones", "tiempo_ms"])
        w.writerows(filas)
    print("\nEn el peor caso las evaluaciones son exactamente n(n+1)/2 y el tiempo crece")
    print("unas 4 veces cada vez que n se duplica: comportamiento cuadratico.")
    print("CSV guardado en: resultados/complejidad.csv")


if __name__ == "__main__":
    main()
