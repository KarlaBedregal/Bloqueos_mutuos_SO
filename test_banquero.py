"""
test_banquero.py - Pruebas automatizadas del gestor de recursos.

Uso: python3 -m unittest -v test_banquero
"""
import unittest

from banquero import DatosInvalidos, GestorRecursos, algoritmo_seguridad, menor_igual, sumar
from demo import ejemplo_clasico, ejemplo_un_recurso
from deteccion import detectar, recuperar


def secuencia_valida(g, secuencia) -> bool:
    """Reproduce la secuencia a mano: cada proceso debe caber en Work cuando le toca."""
    work = list(g.available)
    for i in secuencia:
        if not menor_igual(g.need[i], work):
            return False
        work = sumar(work, g.allocation[i])
    return sorted(secuencia) == list(range(g.n))


class PruebasBanquero(unittest.TestCase):

    # 1) caso seguro con secuencia
    def test_01_estado_inicial_seguro_con_secuencia(self):
        g = ejemplo_clasico()
        r = g.evaluar_estado()
        self.assertEqual(r.estado, "SEGURO")
        self.assertEqual(r.secuencia, [1, 3, 0, 2, 4])          # <P1, P3, P0, P2, P4>
        self.assertTrue(secuencia_valida(g, r.secuencia))

    def test_02_need_se_calcula_como_max_menos_allocation(self):
        g = ejemplo_clasico()
        self.assertEqual(g.need, [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]])
        self.assertEqual(g.available, [3, 3, 2])                # total - suma de Allocation

    # 2) solicitud valida y segura
    def test_03_solicitud_segura_se_concede_y_actualiza(self):
        g = ejemplo_clasico()
        r = g.solicitar("P1", [1, 0, 2])
        self.assertEqual(r.estado, "CONCEDIDA")
        self.assertEqual(g.available, [2, 3, 0])
        self.assertEqual(g.allocation[1], [3, 0, 2])
        self.assertEqual(g.need[1], [0, 2, 0])
        self.assertTrue(secuencia_valida(g, r.secuencia))

    # 3) solicitud valida pero insegura
    def test_04_solicitud_valida_pero_insegura_se_posterga(self):
        g = ejemplo_clasico()
        g.solicitar("P1", [1, 0, 2])
        antes = g.instantanea()
        r = g.solicitar("P0", [0, 2, 0])
        self.assertEqual(r.estado, "POSTERGADA")
        self.assertIn("INSEGURO", r.motivo)
        self.assertEqual(g.instantanea(), antes)

    # 4) solicitud superior a Need
    def test_05_solicitud_superior_a_need_es_error(self):
        g = ejemplo_clasico()
        antes = g.instantanea()
        r = g.solicitar("P1", [2, 0, 0])
        self.assertEqual(r.estado, "ERROR")
        self.assertIn("Need en A es 1", r.motivo)
        self.assertEqual(g.instantanea(), antes)

    # 5) solicitud superior a Available
    def test_06_solicitud_superior_a_available_espera(self):
        g = ejemplo_clasico()
        antes = g.instantanea()
        r = g.solicitar("P0", [4, 0, 0])
        self.assertEqual(r.estado, "EN ESPERA")
        self.assertEqual(g.instantanea(), antes)

    # 6) datos invalidos sin alterar el estado
    def test_07_solicitudes_invalidas_no_alteran_el_estado(self):
        g = ejemplo_clasico()
        antes = g.instantanea()
        for proc, req in [("P7", [1, 0, 0]), ("P1", [1, 0]), ("P1", [1, -1, 0]),
                          ("P1", [1, "x", 0]), ("P1", [0, 0, 0]), (9, [1, 0, 0])]:
            with self.subTest(proceso=proc, request=req):
                self.assertEqual(g.solicitar(proc, req).estado, "ERROR")
        self.assertEqual(g.liberar("P3", [3, 0, 0]).estado, "ERROR")
        self.assertEqual(g.instantanea(), antes)

    def test_08_datos_iniciales_invalidos_se_rechazan(self):
        casos = {
            "Allocation > Max": dict(max_=[[2, 2]], allocation=[[3, 0]], available=[1, 1]),
            "asignado > total": dict(max_=[[4], [4]], allocation=[[3], [3]], total=[5]),
            "filas desiguales": dict(max_=[[2, 2], [1]], allocation=[[1, 1], [1]],
                                     available=[1, 1]),
            "negativo": dict(max_=[[2]], allocation=[[-1]], available=[1]),
            "sin available ni total": dict(max_=[[2]], allocation=[[1]]),
            "available y total a la vez": dict(max_=[[2]], allocation=[[1]],
                                               available=[1], total=[2]),
        }
        for nombre, datos in casos.items():
            with self.subTest(caso=nombre):
                with self.assertRaises(DatosInvalidos):
                    GestorRecursos(**datos)

    # 7) un solo recurso (diapositiva 13)
    def test_09_ejemplo_un_recurso_diapositiva_13(self):
        g = ejemplo_un_recurso()
        r = g.evaluar_estado()
        self.assertEqual([g.procesos[i] for i in r.secuencia], ["P1", "P2", "P3"])
        self.assertEqual(g.solicitar("P3", [3]).estado, "POSTERGADA")

    def test_10_liberar_devuelve_recursos(self):
        g = ejemplo_clasico()
        r = g.liberar("P2", [3, 0, 0])
        self.assertEqual(r.estado, "LIBERADA")
        self.assertEqual(g.available, [6, 3, 2])
        self.assertEqual(g.need[2], [9, 0, 0])

    # 8) deteccion y recuperacion
    def test_11_deteccion_encuentra_interbloqueo_sin_evitacion(self):
        av, al = [2, 1, 0], [[0, 3, 0], [3, 0, 2], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
        req = [[7, 2, 3], [0, 2, 0], [6, 0, 0], [0, 1, 1], [4, 3, 1]]
        nombres, rec = [f"P{i}" for i in range(5)], ["A", "B", "C"]
        det = detectar(av, al, req, nombres, rec)
        self.assertEqual(det.bloqueados, [0, 1, 2, 3, 4])
        abortados, _ = recuperar(av, al, req, nombres, rec)
        self.assertEqual(abortados, [4])

    def test_12_proceso_sin_recursos_no_forma_parte_del_bloqueo(self):
        # P1 espera pero no retiene nada -> Finish inicial = T
        det = detectar([0], [[1], [0]], [[1], [1]], ["P0", "P1"], ["R"])
        self.assertEqual(det.bloqueados, [0])

    def test_13_peor_caso_hace_n_por_n_mas_1_entre_2_evaluaciones(self):
        n = 30
        res = algoritmo_seguridad([1], [[1]] * n, [[n - i] for i in range(n)], registrar=False)
        self.assertTrue(res.completo)
        self.assertEqual(res.evaluaciones, n * (n + 1) // 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
