from AgenteIA.Agente import Agente
import time
import numpy as np
from Estado import ElEstado


class AgenteJugador(Agente):
    DEFAULT_WEIGHTS = [4, 120, 35, 18, 8, 12]
    GENETIC_WEIGHTS = [6, 145, 42, 24, 10, 16]
    POSITION_WEIGHTS = np.array([
        [120, -20, 20, 5, 5, 20, -20, 120],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [120, -20, 20, 5, 5, 20, -20, 120],
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
            return ElEstado(
                jugador=3 - estado.jugador,
                tablero=np.copy(estado.tablero),
                movidas=self._get_valid_moves(estado.tablero, 3 - estado.jugador),
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

        # Si el rival no puede jugar, el turno vuelve al jugador actual.
        mis_movidas = self._get_valid_moves(tablero, estado.jugador)
        return ElEstado(
            jugador=estado.jugador,
            tablero=tablero,
            movidas=mis_movidas,
            get_utilidad=0
        )

    def _corner_positions(self, size):
        return [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]

    def _danger_zones(self, size):
        return {
            (0, 0): [(0, 1), (1, 0), (1, 1)],
            (0, size - 1): [(0, size - 2), (1, size - 1), (1, size - 2)],
            (size - 1, 0): [(size - 2, 0), (size - 1, 1), (size - 2, 1)],
            (size - 1, size - 1): [(size - 2, size - 1), (size - 1, size - 2), (size - 2, size - 2)],
        }

    def funcion_evaluacion(self, estado, jugador_base=None):
        tablero = estado.tablero
        jugador = estado.jugador if jugador_base is None else jugador_base
        rival = 3 - jugador
        size = len(tablero)

        w_fichas, w_esquinas, w_peligro, w_movilidad, w_bordes, w_posicional = self.pesos

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
            if tablero[esquina[0]][esquina[1]] != 0:
                continue
            for r, c in celdas:
                if tablero[r][c] == jugador:
                    score_peligro -= 1
                elif tablero[r][c] == rival:
                    score_peligro += 1

        mis_movidas = len(self._get_valid_moves(tablero, jugador))
        mov_rival = len(self._get_valid_moves(tablero, rival))
        score_movilidad = mis_movidas - mov_rival

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

        return (
            w_fichas * score_fichas +
            w_esquinas * score_esquinas +
            w_peligro * score_peligro +
            w_movilidad * score_movilidad +
            w_bordes * score_bordes +
            w_posicional * score_posicional
        )

    def podaAlphaBeta_eval(self, estado):
        jugador_raiz = estado.jugador

        def evaluar(e):
            if self.testTerminal(e):
                tablero = e.tablero
                return int(np.sum(tablero == jugador_raiz) - np.sum(tablero == (3 - jugador_raiz))) * 10000
            return self.funcion_evaluacion(e, jugador_raiz)

        def max_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return evaluar(e)

            acciones = self.jugadas(e)
            if not acciones:
                return min_value(
                    ElEstado(jugador=3 - e.jugador, tablero=e.tablero, movidas=self._get_valid_moves(e.tablero, 3 - e.jugador), get_utilidad=0),
                    alpha,
                    beta,
                    profundidad + 1,
                )

            v = -float('inf')
            for accion in acciones:
                v = max(v, min_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v >= beta:
                    return v
                alpha = max(alpha, v)
            return v

        def min_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return evaluar(e)

            acciones = self.jugadas(e)
            if not acciones:
                return max_value(
                    ElEstado(jugador=3 - e.jugador, tablero=e.tablero, movidas=self._get_valid_moves(e.tablero, 3 - e.jugador), get_utilidad=0),
                    alpha,
                    beta,
                    profundidad + 1,
                )

            v = float('inf')
            for accion in acciones:
                v = min(v, max_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v

        acciones = self.jugadas(estado)
        if not acciones:
            return None

        mejor_score = -float('inf')
        beta = float('inf')
        mejor_accion = acciones[0]

        # Ordena para explorar primero jugadas prometedoras y mejorar la poda.
        acciones_ordenadas = sorted(
            acciones,
            key=lambda accion: self.funcion_evaluacion(self.getResultado(estado, accion), jugador_raiz),
            reverse=True,
        )

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
