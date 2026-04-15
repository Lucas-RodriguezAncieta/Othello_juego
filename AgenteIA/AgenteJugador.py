from AgenteIA.Agente import Agente
import time
import numpy as np
from Estado import ElEstado


class AgenteJugador(Agente):
    DEFAULT_WEIGHTS = [4, 120, 35, 18, 8, 12]
    GENETIC_WEIGHTS = [6, 145, 42, 24, 10, 16]

    POSITION_WEIGHTS = np.array([
        [120, -20,  20,   5,   5,  20, -20, 120],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [ 20,  -5,  15,   3,   3,  15,  -5,  20],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [ 20,  -5,  15,   3,   3,  15,  -5,  20],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [120, -20,  20,   5,   5,  20, -20, 120],
    ])

    def __init__(self, altura=4, pesos=None, usar_genetico=True):
        super().__init__()
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta"

        if pesos is not None:
            self.pesos = list(pesos)
        elif usar_genetico:
            self.pesos = self.GENETIC_WEIGHTS.copy()
        else:
            self.pesos = self.DEFAULT_WEIGHTS.copy()

    def jugadas(self, estado):
        return estado.movidas

    def get_utilidad(self, estado, jugador):
        raise NotImplementedError

    def testTerminal(self, estado):
        if estado.movidas:
            return False
        rival = 3 - estado.jugador
        return not self._get_valid_moves(estado.tablero, rival)

    def _directions(self):
        return [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ]

    def _corner_positions(self, size):
        return [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]

    def _danger_zones(self, size):
        return {
            (0, 0): [(0, 1), (1, 0), (1, 1)],
            (0, size - 1): [(0, size - 2), (1, size - 1), (1, size - 2)],
            (size - 1, 0): [(size - 2, 0), (size - 1, 1), (size - 2, 1)],
            (size - 1, size - 1): [(size - 2, size - 1), (size - 1, size - 2), (size - 2, size - 2)],
        }

    def _count_stable_discs(self, tablero, jugador):
        size = len(tablero)
        estable = set()
        esquinas = self._corner_positions(size)

        def avanzar(fila, col, paso_fila, paso_col):
            while 0 <= fila < size and 0 <= col < size and tablero[fila][col] == jugador:
                estable.add((fila, col))
                fila += paso_fila
                col += paso_col

        if tablero[0][0] == jugador:
            avanzar(0, 0, 0, 1)
            avanzar(0, 0, 1, 0)
        if tablero[0][size - 1] == jugador:
            avanzar(0, size - 1, 0, -1)
            avanzar(0, size - 1, 1, 0)
        if tablero[size - 1][0] == jugador:
            avanzar(size - 1, 0, 0, 1)
            avanzar(size - 1, 0, -1, 0)
        if tablero[size - 1][size - 1] == jugador:
            avanzar(size - 1, size - 1, 0, -1)
            avanzar(size - 1, size - 1, -1, 0)

        # Extensión conservadora en bordes completos entre extremos ya asegurados.
        for fila in [0, size - 1]:
            if all(tablero[fila][col] == jugador for col in range(size)):
                for col in range(size):
                    estable.add((fila, col))
        for col in [0, size - 1]:
            if all(tablero[fila][col] == jugador for fila in range(size)):
                for fila in range(size):
                    estable.add((fila, col))

        return len(estable)

    def _parity_score(self, tablero, jugador):
        vacias = int(np.sum(tablero == 0))
        if vacias == 0:
            return 0

        # En Othello, mover con paridad favorable en el final suele ser ventajoso.
        # Valor positivo si el jugador base tendrá la última jugada bajo paridad simple.
        return 1 if vacias % 2 == 1 else -1

    def _is_valid_move(self, tablero, jugador, row, col):
        if tablero[row][col] != 0:
            return False

        rival = 3 - jugador
        size = len(tablero)

        for dr, dc in self._directions():
            r, c = row + dr, col + dc
            found_opponent = False

            while 0 <= r < size and 0 <= c < size and tablero[r][c] == rival:
                found_opponent = True
                r += dr
                c += dc

            if found_opponent and 0 <= r < size and 0 <= c < size and tablero[r][c] == jugador:
                return True

        return False

    def _get_valid_moves(self, tablero, jugador):
        size = len(tablero)
        return [
            (r, c)
            for r in range(size)
            for c in range(size)
            if self._is_valid_move(tablero, jugador, r, c)
        ]

    def _apply_move(self, tablero, jugador, accion):
        nuevo_tablero = np.copy(tablero)
        row, col = accion
        rival = 3 - jugador
        nuevo_tablero[row][col] = jugador

        for dr, dc in self._directions():
            r, c = row + dr, col + dc
            piezas_a_voltear = []

            while 0 <= r < len(nuevo_tablero) and 0 <= c < len(nuevo_tablero) and nuevo_tablero[r][c] == rival:
                piezas_a_voltear.append((r, c))
                r += dr
                c += dc

            if 0 <= r < len(nuevo_tablero) and 0 <= c < len(nuevo_tablero) and nuevo_tablero[r][c] == jugador:
                for rr, cc in piezas_a_voltear:
                    nuevo_tablero[rr][cc] = jugador

        return nuevo_tablero

    def _build_state(self, tablero, jugador):
        return ElEstado(
            jugador=jugador,
            tablero=tablero,
            movidas=self._get_valid_moves(tablero, jugador),
            get_utilidad=0
        )

    def getResultado(self, estado, accion):
        if accion is None:
            rival = 3 - estado.jugador
            return ElEstado(
                jugador=rival,
                tablero=np.copy(estado.tablero),
                movidas=self._get_valid_moves(estado.tablero, rival),
                get_utilidad=0
            )

        tablero = self._apply_move(estado.tablero, estado.jugador, accion)
        siguiente_jugador = 3 - estado.jugador
        nuevas_movidas = self._get_valid_moves(tablero, siguiente_jugador)

        if nuevas_movidas:
            return ElEstado(
                jugador=siguiente_jugador,
                tablero=tablero,
                movidas=nuevas_movidas,
                get_utilidad=0
            )

        # Si el rival no puede jugar, el turno vuelve al jugador actual
        mis_movidas = self._get_valid_moves(tablero, estado.jugador)
        return ElEstado(
            jugador=estado.jugador,
            tablero=tablero,
            movidas=mis_movidas,
            get_utilidad=0
        )

    def funcion_evaluacion(self, estado, jugador_base=None):
        tablero = estado.tablero
        jugador = estado.jugador if jugador_base is None else jugador_base
        rival = 3 - jugador
        size = len(tablero)

        casillas_vacias = int(np.sum(tablero == 0))
        base_fichas, base_esquinas, base_peligro, base_movilidad, base_bordes, base_posicional = self.pesos

        # Ajuste dinámico por fases, respetando los pesos configurados/genéticos.
        if casillas_vacias > 40:
            multipliers = [0.4, 1.0, 1.0, 2.0, 0.7, 0.8]
        elif casillas_vacias > 15:
            multipliers = [0.8, 1.15, 1.1, 1.3, 1.0, 1.0]
        else:
            multipliers = [1.8, 1.35, 0.7, 0.4, 1.1, 1.2]

        w_fichas = base_fichas * multipliers[0]
        w_esquinas = base_esquinas * multipliers[1]
        w_peligro = base_peligro * multipliers[2]
        w_movilidad = base_movilidad * multipliers[3]
        w_bordes = base_bordes * multipliers[4]
        w_posicional = base_posicional * multipliers[5]
        w_estabilidad = (base_esquinas * 0.35) * (0.5 if casillas_vacias > 40 else 1.0 if casillas_vacias > 15 else 1.6)
        w_paridad = (base_movilidad * 0.8) * (0.0 if casillas_vacias > 15 else 1.8)

        fichas_jugador = int(np.sum(tablero == jugador))
        fichas_rival = int(np.sum(tablero == rival))
        score_fichas = fichas_jugador - fichas_rival

        esquinas = self._corner_positions(size)
        score_esquinas = sum(
            1 if tablero[r][c] == jugador else -1 if tablero[r][c] == rival else 0
            for r, c in esquinas
        )

        score_peligro = 0
        for esquina, celdas in self._danger_zones(size).items():
            # Solo castiga estas celdas si la esquina aún está libre
            if tablero[esquina[0]][esquina[1]] != 0:
                continue
            for r, c in celdas:
                if tablero[r][c] == jugador:
                    score_peligro -= 1
                elif tablero[r][c] == rival:
                    score_peligro += 1

        mis_movidas = len(self._get_valid_moves(tablero, jugador))
        mov_rival = len(self._get_valid_moves(tablero, rival))
        if mis_movidas + mov_rival != 0:
            score_movilidad = (mis_movidas - mov_rival) / (mis_movidas + mov_rival)
        else:
            score_movilidad = 0

        score_bordes = 0
        for i in range(size):
            for j in range(size):
                if (i, j) in esquinas:
                    continue
                if i in [0, size - 1] or j in [0, size - 1]:
                    if tablero[i][j] == jugador:
                        score_bordes += 1
                    elif tablero[i][j] == rival:
                        score_bordes -= 1

        if size == 8:
            score_posicional = int(np.sum(self.POSITION_WEIGHTS * (tablero == jugador)))
            score_posicional -= int(np.sum(self.POSITION_WEIGHTS * (tablero == rival)))
        else:
            score_posicional = 0

        score_estabilidad = self._count_stable_discs(tablero, jugador) - self._count_stable_discs(tablero, rival)
        score_paridad = self._parity_score(tablero, jugador)

        return (
            w_fichas * score_fichas +
            w_esquinas * score_esquinas +
            w_peligro * score_peligro +
            w_movilidad * score_movilidad +
            w_bordes * score_bordes +
            w_posicional * score_posicional +
            w_estabilidad * score_estabilidad +
            w_paridad * score_paridad
        )

    def podaAlphaBeta_eval(self, estado):
        jugador_raiz = estado.jugador
        size = len(estado.tablero)

        def evaluar(e):
            if self.testTerminal(e):
                tablero = e.tablero
                return int(np.sum(tablero == jugador_raiz) - np.sum(tablero == (3 - jugador_raiz))) * 10000
            return self.funcion_evaluacion(e, jugador_raiz)

        def max_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return evaluar(e)

            acciones_locales = [tuple(a) for a in self.jugadas(e)]

            if not acciones_locales:
                return min_value(
                    ElEstado(
                        jugador=3 - e.jugador,
                        tablero=e.tablero,
                        movidas=self._get_valid_moves(e.tablero, 3 - e.jugador),
                        get_utilidad=0
                    ),
                    alpha,
                    beta,
                    profundidad + 1,
                )

            v = -float('inf')
            for accion in acciones_locales:
                v = max(v, min_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v >= beta:
                    return v
                alpha = max(alpha, v)
            return v

        def min_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return evaluar(e)

            acciones_locales = [tuple(a) for a in self.jugadas(e)]

            if not acciones_locales:
                return max_value(
                    ElEstado(
                        jugador=3 - e.jugador,
                        tablero=e.tablero,
                        movidas=self._get_valid_moves(e.tablero, 3 - e.jugador),
                        get_utilidad=0
                    ),
                    alpha,
                    beta,
                    profundidad + 1,
                )

            v = float('inf')
            for accion in acciones_locales:
                v = min(v, max_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v

        # 🔥 ACCIONES RAÍZ (fix tuplas)
        acciones = [tuple(a) for a in self.jugadas(estado)]
        if not acciones:
            return None

        # 🧨 PRIORIDAD ABSOLUTA A ESQUINAS
        esquinas = set(self._corner_positions(size))
        for accion in acciones:
            if accion in esquinas:
                return accion

        # 🔥 ORDENAMIENTO (mejor poda)
        acciones_ordenadas = sorted(
            acciones,
            key=lambda accion: self.funcion_evaluacion(
                self.getResultado(estado, accion), jugador_raiz
            ),
            reverse=True
        )

        mejor_score = -float('inf')
        beta = float('inf')
        mejor_accion = acciones_ordenadas[0]

        for accion in acciones_ordenadas:
            v = min_value(self.getResultado(estado, accion), mejor_score, beta, 1)
            if v > mejor_score:
                mejor_score = v
                mejor_accion = accion

        return mejor_accion

    def mide_tiempo(funcion):
        def funcion_medida(*args, **kwargs):
            _inicio = time.time()
            return funcion(*args, **kwargs)
        return funcion_medida

    @mide_tiempo
    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return

        self.set_acciones(self.podaAlphaBeta_eval(self.estado))
