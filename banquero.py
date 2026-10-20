"""
banquero.py - Gestor de recursos seguro (algoritmo del banquero).

Sistemas Operativos - UNSA - 2026-B - Semana 8: Bloqueos mutuos
Practica domiciliaria: gestor con N procesos y M tipos de recurso.

El gestor recibe Max (demanda maxima declarada), Allocation (asignacion actual)
y Available (o el total de cada recurso), calcula Need = Max - Allocation y
atiende solicitudes dinamicas:

    1. verifica Request <= Need[i]       (no pedir mas de lo declarado)
    2. verifica Request <= Available     (si no, el proceso espera)
    3. simula la asignacion en una COPIA del estado
    4. ejecuta la prueba de seguridad sobre la copia
    5. concede solo si existe una secuencia segura

El estado real solo se modifica en el paso 5. Si los datos son invalidos o la
solicitud se posterga, el estado queda exactamente igual.

Uso:
    python3 banquero.py estado_ejemplo.json                        (modo interactivo)
    python3 banquero.py estado_ejemplo.json solicitudes_ejemplo.txt (lee comandos de un archivo)
"""
from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field


class DatosInvalidos(ValueError):
    """Error en los datos de entrada. Se lanza ANTES de tocar el estado."""


# --------------------------------------------------------------- vectores
def vec(v) -> str:
    return "(" + ", ".join(str(x) for x in v) + ")"


def menor_igual(a, b) -> bool:
    return all(x <= y for x, y in zip(a, b))


def sumar(a, b) -> list:
    return [x + y for x, y in zip(a, b)]


def restar(a, b) -> list:
    return [x - y for x, y in zip(a, b)]


def primer_exceso(a, b):
    """Primer indice j donde a[j] > b[j], o None si a <= b."""
    for j, (x, y) in enumerate(zip(a, b)):
        if x > y:
            return j
    return None


def texto_finish(finish) -> str:
    return "[" + ", ".join("T" if f else "F" for f in finish) + "]"


# ------------------------------------------------- validacion de entradas
def _es_entero(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _validar_vector(v, m, nombre, recursos) -> list:
    if not isinstance(v, (list, tuple)):
        raise DatosInvalidos(f"{nombre} debe ser una lista de {m} enteros")
    if len(v) != m:
        raise DatosInvalidos(
            f"{nombre} tiene {len(v)} valores y se esperaban {m} (uno por tipo de recurso)")
    for j, x in enumerate(v):
        if not _es_entero(x):
            raise DatosInvalidos(f"{nombre} en {recursos[j]} = {x!r} no es un entero")
        if x < 0:
            raise DatosInvalidos(f"{nombre} en {recursos[j]} = {x} es negativo")
    return list(v)


def _validar_matriz(mat, n, m, nombre, procesos, recursos) -> list:
    if not isinstance(mat, (list, tuple)) or len(mat) != n:
        raise DatosInvalidos(f"{nombre} debe tener {n} filas (una por proceso)")
    return [_validar_vector(f, m, f"{nombre}[{procesos[i]}]", recursos)
            for i, f in enumerate(mat)]


# --------------------------------------------- simulacion de finalizacion
@dataclass
class Paso:
    numero: int
    work_antes: list
    finish_antes: list
    revisados: list            # (i, cumple, j_fallo) en el orden revisado
    elegido: int | None        # None: ningun proceso pudo avanzar
    work_despues: list


@dataclass
class ResultadoSimulacion:
    completo: bool             # True si todos los procesos terminan
    secuencia: list            # indices en el orden en que terminan
    pasos: list
    work_final: list
    finish_final: list
    evaluaciones: int = 0      # cuantas veces se comparo Demanda[i] <= Work


def simular_finalizacion(work0, allocation, demanda, finish0, registrar=True):
    """Nucleo comun de la prueba de seguridad y de la deteccion.

    Busca un proceso i con Finish[i] = F y Demanda[i] <= Work, simula que termina
    (Work += Allocation[i], Finish[i] = T) y vuelve a empezar la busqueda desde
    el primer proceso. Termina cuando todos acaban o ninguno puede avanzar.
    - prueba de seguridad: Demanda = Need,    Finish inicial todo F
    - deteccion:           Demanda = Request, Finish inicial T si Allocation = 0
    """
    n = len(allocation)
    work = list(work0)
    finish = list(finish0)
    secuencia, pasos = [], []
    evaluaciones = 0
    numero = 0
    while not all(finish):
        numero += 1
        work_antes, finish_antes = list(work), list(finish)
        revisados, elegido = [], None
        for i in range(n):
            if finish[i]:
                continue
            evaluaciones += 1
            j = primer_exceso(demanda[i], work)
            revisados.append((i, j is None, j))
            if j is None:
                elegido = i
                break
        if elegido is None:
            if registrar:
                pasos.append(Paso(numero, work_antes, finish_antes, revisados, None, list(work)))
            break
        work = sumar(work, allocation[elegido])
        finish[elegido] = True
        secuencia.append(elegido)
        if registrar:
            pasos.append(Paso(numero, work_antes, finish_antes, revisados, elegido, list(work)))
    return ResultadoSimulacion(all(finish), secuencia, pasos, work, finish, evaluaciones)


def algoritmo_seguridad(available, allocation, need, registrar=True):
    """Devuelve el resultado de la prueba de seguridad (no modifica nada)."""
    return simular_finalizacion(available, allocation, need, [False] * len(allocation),
                                registrar)


def formatear_traza(res, available, allocation, demanda, procesos, recursos,
                    etiqueta="Need") -> list:
    """Traza paso a paso con Available, Work y Finish (T = termina, F = pendiente)."""
    lineas = []
    for p in res.pasos:
        lineas.append(f"Paso {p.numero} | Available = {vec(available)} | Work = "
                      f"{vec(p.work_antes)} | Finish = {texto_finish(p.finish_antes)}")
        for i, cumple, j in p.revisados:
            base = f"   {procesos[i]}: {etiqueta} {vec(demanda[i])} <= Work?"
            if cumple:
                lineas.append(f"{base} SI -> puede terminar y libera "
                              f"Allocation {vec(allocation[i])}")
            else:
                lineas.append(f"{base} NO (en {recursos[j]} necesita "
                              f"{demanda[i][j]} y Work tiene {p.work_antes[j]})")
        if p.elegido is None:
            pend = ", ".join(procesos[i] for i, f in enumerate(p.finish_antes) if not f)
            lineas.append(f"   Ningun proceso pendiente cumple {etiqueta} <= Work. "
                          f"Quedan sin terminar: {pend}")
        else:
            lineas.append(f"   Work = {vec(p.work_antes)} + {vec(allocation[p.elegido])} = "
                          f"{vec(p.work_despues)}  ->  Finish[{procesos[p.elegido]}] = T")
    lineas.append(f"Fin    | Available = {vec(available)} | Work = {vec(res.work_final)} | "
                  f"Finish = {texto_finish(res.finish_final)}")
    return lineas


# ----------------------------------------------------------- respuestas
@dataclass
class Respuesta:
    estado: str                # CONCEDIDA, POSTERGADA, EN ESPERA, ERROR, LIBERADA
    motivo: str                # por que se tomo la decision
    lineas: list = field(default_factory=list)
    secuencia: list | None = None

    def __str__(self) -> str:
        return "\n".join(self.lineas + [f"  DECISION: {self.estado}. {self.motivo}"])


# ------------------------------------------------------------ el gestor
class GestorRecursos:
    def __init__(self, max_, allocation, available=None, total=None,
                 recursos=None, procesos=None):
        # Todo se valida en variables locales; el objeto solo se arma si todo es valido.
        if not isinstance(max_, (list, tuple)) or not max_:
            raise DatosInvalidos("Max debe tener al menos un proceso")
        if not isinstance(max_[0], (list, tuple)) or not max_[0]:
            raise DatosInvalidos("Max debe tener al menos un tipo de recurso")
        n, m = len(max_), len(max_[0])
        recursos = list(recursos) if recursos else [chr(ord("A") + j) for j in range(m)]
        procesos = list(procesos) if procesos else [f"P{i}" for i in range(n)]
        if len(recursos) != m:
            raise DatosInvalidos(f"se dieron {len(recursos)} nombres de recurso para {m} tipos")
        if len(procesos) != n:
            raise DatosInvalidos(f"se dieron {len(procesos)} nombres de proceso para {n} procesos")
        if len(set(procesos)) != n:
            raise DatosInvalidos("hay nombres de proceso repetidos")

        mx = _validar_matriz(max_, n, m, "Max", procesos, recursos)
        al = _validar_matriz(allocation, n, m, "Allocation", procesos, recursos)
        for i in range(n):
            j = primer_exceso(al[i], mx[i])
            if j is not None:
                raise DatosInvalidos(
                    f"Allocation[{procesos[i]}] > Max[{procesos[i]}] en {recursos[j]} "
                    f"({al[i][j]} > {mx[i][j]}): un proceso no puede tener mas de lo que declaro")

        if (available is None) == (total is None):
            raise DatosInvalidos("se debe dar Available o el total de recursos (solo uno)")
        if total is not None:
            tot = _validar_vector(total, m, "Total", recursos)
            asignado = [sum(al[i][j] for i in range(n)) for j in range(m)]
            av = restar(tot, asignado)
            j = next((k for k, x in enumerate(av) if x < 0), None)
            if j is not None:
                raise DatosInvalidos(
                    f"en {recursos[j]} hay {asignado[j]} unidades asignadas pero el total "
                    f"es {tot[j]}")
        else:
            av = _validar_vector(available, m, "Available", recursos)

        self.n, self.m = n, m
        self.recursos, self.procesos = recursos, procesos
        self.max = mx
        self.allocation = al
        self.available = av
        self.need = self.calcular_need(mx, al)

    # ---------------------------------------------------------- consultas
    @staticmethod
    def calcular_need(max_, allocation) -> list:
        return [restar(fm, fa) for fm, fa in zip(max_, allocation)]

    def instantanea(self) -> tuple:
        """Copia del estado completo, para comprobar que no cambio."""
        return copy.deepcopy((self.available, self.max, self.allocation, self.need))

    def tabla_estado(self) -> list:
        ancho = max(len("Proceso"), max(len(p) for p in self.procesos))
        col = max(len(vec([0] * self.m)), len("Allocation"))
        lineas = [f"  {'Proceso':<{ancho}}  {'Allocation':<{col}}  {'Max':<{col}}  Need"]
        for i, p in enumerate(self.procesos):
            lineas.append(f"  {p:<{ancho}}  {vec(self.allocation[i]):<{col}}  "
                          f"{vec(self.max[i]):<{col}}  {vec(self.need[i])}")
        lineas.append(f"  Available = {vec(self.available)}   (recursos: {', '.join(self.recursos)})")
        return lineas

    def evaluar_estado(self) -> Respuesta:
        res = algoritmo_seguridad(self.available, self.allocation, self.need)
        lineas = [">>> Prueba de seguridad del estado actual"] + self.tabla_estado()
        lineas += ["  " + l for l in formatear_traza(res, self.available, self.allocation,
                                                     self.need, self.procesos, self.recursos)]
        if res.completo:
            sec = self._texto_secuencia(res.secuencia)
            return Respuesta("SEGURO", f"Existe la secuencia segura {sec}: con lo disponible "
                             f"cada proceso puede recibir su Need, terminar y liberar para el "
                             f"siguiente.", lineas, res.secuencia)
        pend = ", ".join(self.procesos[i] for i, f in enumerate(res.finish_final) if not f)
        return Respuesta("INSEGURO", f"No se puede demostrar una secuencia completa; "
                         f"{pend} no pueden garantizar su terminacion.", lineas)

    # --------------------------------------------------------- operaciones
    def solicitar(self, proceso, request) -> Respuesta:
        try:
            i = self._indice(proceso)
            req = _validar_vector(request, self.m, "Request", self.recursos)
        except DatosInvalidos as e:
            return Respuesta("ERROR", f"Datos invalidos: {e}. El estado no se modifico.",
                             [f">>> Solicitud de {proceso}: Request = {request}"])
        p = self.procesos[i]
        lineas = [f">>> Solicitud de {p}: Request = {vec(req)}",
                  f"  Estado actual: Available = {vec(self.available)} | "
                  f"Allocation[{p}] = {vec(self.allocation[i])} | Need[{p}] = {vec(self.need[i])}"]
        if not any(req):
            return Respuesta("ERROR", "La solicitud no pide ninguna unidad. "
                             "El estado no se modifico.", lineas)

        # 1) Request <= Need[i]
        j = primer_exceso(req, self.need[i])
        ok = "SI" if j is None else f"NO (en {self.recursos[j]}: {req[j]} > {self.need[i][j]})"
        lineas.append(f"  [1] Request <= Need[{p}]?  {vec(req)} <= {vec(self.need[i])} -> {ok}")
        if j is not None:
            r = self.recursos[j]
            return Respuesta("ERROR", f"{p} pide {req[j]} unidades de {r}, pero su Need en {r} es "
                             f"{self.need[i][j]} (Max {self.max[i][j]} - Allocation "
                             f"{self.allocation[i][j]}). Pedir mas de lo que declaro como maximo "
                             f"rompe el contrato del banquero. El estado no se modifico.", lineas)

        # 2) Request <= Available
        j = primer_exceso(req, self.available)
        ok = "SI" if j is None else f"NO (en {self.recursos[j]}: {req[j]} > {self.available[j]})"
        lineas.append(f"  [2] Request <= Available?  {vec(req)} <= {vec(self.available)} -> {ok}")
        if j is not None:
            return Respuesta("EN ESPERA", f"La solicitud es valida, pero ahora solo hay "
                             f"{self.available[j]} unidades libres de {self.recursos[j]} y pide "
                             f"{req[j]}. {p} debe esperar a que otro proceso libere recursos. "
                             f"El estado no se modifico.", lineas)

        # 3) simular la asignacion sobre copias
        av = restar(self.available, req)
        al = copy.deepcopy(self.allocation)
        nd = copy.deepcopy(self.need)
        al[i] = sumar(al[i], req)
        nd[i] = restar(nd[i], req)
        lineas += ["  [3] Simulacion de la asignacion (en una copia del estado):",
                   f"        Available  = {vec(self.available)} - {vec(req)} = {vec(av)}",
                   f"        Allocation[{p}] = {vec(self.allocation[i])} + {vec(req)} = {vec(al[i])}",
                   f"        Need[{p}]  = {vec(self.need[i])} - {vec(req)} = {vec(nd[i])}"]

        # 4) prueba de seguridad del estado simulado
        res = algoritmo_seguridad(av, al, nd)
        lineas.append("  [4] Prueba de seguridad sobre el estado simulado:")
        lineas += ["        " + l for l in
                   formatear_traza(res, av, al, nd, self.procesos, self.recursos)]

        # 5) conceder solo si existe secuencia segura
        if not res.completo:
            pend = ", ".join(self.procesos[k] for k, f in enumerate(res.finish_final) if not f)
            return Respuesta("POSTERGADA", f"La solicitud es valida y hay recursos libres, pero "
                             f"si se concede el sistema queda en un estado INSEGURO: con Work = "
                             f"{vec(res.work_final)} ninguno de {pend} puede asegurar su "
                             f"terminacion. Se descarta la simulacion y {p} debe esperar. "
                             f"El estado no se modifico.", lineas)

        self.available, self.allocation, self.need = av, al, nd   # se confirma
        sec = self._texto_secuencia(res.secuencia)
        return Respuesta("CONCEDIDA", f"El estado resultante es seguro porque existe la secuencia "
                         f"{sec}. Se confirma la asignacion: Available = {vec(av)}.",
                         lineas, res.secuencia)

    def liberar(self, proceso, vector) -> Respuesta:
        try:
            i = self._indice(proceso)
            rel = _validar_vector(vector, self.m, "Release", self.recursos)
        except DatosInvalidos as e:
            return Respuesta("ERROR", f"Datos invalidos: {e}. El estado no se modifico.",
                             [f">>> Liberacion de {proceso}: {vector}"])
        p = self.procesos[i]
        lineas = [f">>> Liberacion de {p}: Release = {vec(rel)}"]
        j = primer_exceso(rel, self.allocation[i])
        if j is not None:
            return Respuesta("ERROR", f"{p} intenta liberar {rel[j]} de {self.recursos[j]} pero solo "
                             f"tiene {self.allocation[i][j]} asignadas. El estado no se modifico.",
                             lineas)
        antes = list(self.available)
        self.available = sumar(self.available, rel)
        self.allocation[i] = restar(self.allocation[i], rel)
        self.need[i] = sumar(self.need[i], rel)
        return Respuesta("LIBERADA", f"Available = {vec(antes)} + {vec(rel)} = "
                         f"{vec(self.available)}. Liberar nunca vuelve inseguro un estado.", lineas)

    # ------------------------------------------------------------ apoyo
    def _indice(self, proceso) -> int:
        if _es_entero(proceso) and 0 <= proceso < self.n:
            return proceso
        if isinstance(proceso, str) and proceso in self.procesos:
            return self.procesos.index(proceso)
        raise DatosInvalidos(f"el proceso {proceso!r} no existe "
                             f"(procesos validos: {', '.join(self.procesos)})")

    def _texto_secuencia(self, secuencia) -> str:
        return "<" + ", ".join(self.procesos[k] for k in secuencia) + ">"

    @classmethod
    def desde_json(cls, ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise DatosInvalidos(f"no se pudo leer {ruta}: {e}")
        if not isinstance(d, dict) or "max" not in d or "allocation" not in d:
            raise DatosInvalidos("el JSON debe tener las claves 'max' y 'allocation'")
        return cls(d["max"], d["allocation"], available=d.get("available"),
                   total=d.get("total"), recursos=d.get("recursos"), procesos=d.get("procesos"))


# ------------------------------------------------------------ modo consola
AYUDA = """Comandos:
  estado                      muestra Allocation, Max, Need y Available
  seguro                      ejecuta la prueba de seguridad del estado actual
  solicitar <proceso> <v...>  ej: solicitar P1 1 0 2
  liberar <proceso> <v...>    ej: liberar P1 1 0 0
  ayuda | salir"""


def ejecutar_comando(g: GestorRecursos, linea: str):
    partes = linea.split()
    if not partes:
        return True
    cmd, args = partes[0].lower(), partes[1:]
    if cmd in ("salir", "exit", "q"):
        return False
    if cmd == "ayuda":
        print(AYUDA)
    elif cmd == "estado":
        print("\n".join(g.tabla_estado()))
    elif cmd == "seguro":
        print(g.evaluar_estado())
    elif cmd in ("solicitar", "liberar"):
        if not args:
            print("  ERROR: falta el proceso. " + AYUDA.splitlines()[3].strip())
            return True
        try:
            valores = [int(x) for x in args[1:]]
        except ValueError:
            print(f"  ERROR: los valores deben ser enteros: {' '.join(args[1:])}. "
                  f"El estado no se modifico.")
            return True
        op = g.solicitar if cmd == "solicitar" else g.liberar
        print(op(args[0], valores))
    else:
        print(f"  Comando desconocido: {cmd}. Escribe 'ayuda'.")
    return True


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    try:
        g = GestorRecursos.desde_json(argv[1])
    except DatosInvalidos as e:
        print(f"ERROR en los datos iniciales: {e}")
        return 1
    print(f"Gestor cargado: {g.n} procesos, {g.m} tipos de recurso")
    print("\n".join(g.tabla_estado()))
    if len(argv) >= 3:                                   # comandos desde un archivo
        with open(argv[2], encoding="utf-8") as f:
            for linea in f:
                linea = linea.split("#", 1)[0].strip()
                if linea:
                    print(f"\n$ {linea}")
                    if not ejecutar_comando(g, linea):
                        break
        return 0
    print("\n" + AYUDA)
    while True:                                          # solicitudes dinamicas
        try:
            linea = input("\nbanquero> ")
        except EOFError:
            break
        if not ejecutar_comando(g, linea):
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
