from AgenteIA.Agente import Agente
import time
import numpy as np
from TableroOthello import TableroOthello
from Estado import ElEstado

class AgenteJugador(Agente):
    def __init__(self, altura=3):
        Agente.__init__(self)
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta" # Por defecto
        self.pesos = [2, 100, -30, 10, 5]  # valores iniciales

    def jugadas(self, estado):
        return estado.movidas

    def get_utilidad(self, estado, jugador):
        raise NotImplementedError

    def testTerminal(self, estado):
        return not estado.movidas

    def getResultado(self, estado, accion):

        tablero = np.copy(estado.tablero)
        jugador = estado.jugador
        rival = 3 - jugador
        row, col = accion

        # Colocar ficha
        tablero[row][col] = jugador

        # Direcciones Othello
        directions = [(-1, -1), (-1, 0), (-1, 1),
                    (0, -1),          (0, 1),
                    (1, -1),  (1, 0), (1, 1)]

        # Voltear fichas
        for dr, dc in directions:
            r, c = row + dr, col + dc
            piezas_a_voltear = []

            while 0 <= r < len(tablero) and 0 <= c < len(tablero) and tablero[r][c] == rival:
                piezas_a_voltear.append((r, c))
                r += dr
                c += dc

            if 0 <= r < len(tablero) and 0 <= c < len(tablero) and tablero[r][c] == jugador:
                for rr, cc in piezas_a_voltear:
                    tablero[rr][cc] = jugador

        # Cambiar jugador
        siguiente_jugador = rival

        # Obtener nuevas jugadas
        temp = TableroOthello(len(tablero))
        nuevas_movidas = temp._get_valid_moves(tablero, siguiente_jugador)

        # Crear nuevo estado
        nuevo_estado = ElEstado(
            jugador=siguiente_jugador,
            tablero=tablero,
            movidas=nuevas_movidas,
            get_utilidad=0
        )

        return nuevo_estado

    def funcion_evaluacion(self, estado):
        

        tablero = estado.tablero
        jugador = estado.jugador
        rival = 3 - jugador
        size = len(tablero)

        # pesos (IMPORTANTE)
        w1, w2, w3, w4, w5 = self.pesos

        # fichas
        fichas_jugador = np.sum(tablero == jugador)
        fichas_rival = np.sum(tablero == rival)
        score_fichas = fichas_jugador - fichas_rival

        # esquinas
        esquinas = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
        score_esquinas = sum(
            1 if tablero[r][c] == jugador else -1 if tablero[r][c] == rival else 0
            for r,c in esquinas
        )

        # peligro
        peligrosas = [(0,1),(1,0),(1,1)]
        score_peligro = sum(
            -1 if tablero[r][c] == jugador else 1 if tablero[r][c] == rival else 0
            for r,c in peligrosas
        )

        # movilidad
        temp = TableroOthello(size)
        mov_rival = len(temp._get_valid_moves(tablero, rival))
        score_movilidad = len(estado.movidas) - mov_rival

        # bordes
        score_bordes = 0
        for i in range(size):
            for j in range(size):
                if i in [0,size-1] or j in [0,size-1]:
                    if tablero[i][j] == jugador:
                        score_bordes += 1
                    elif tablero[i][j] == rival:
                        score_bordes -= 1
        # [2, 100, -30, 10, 5]  # valores iniciales sin uso de algoritmo genetico
        return (
            w1 * score_fichas +
            w2 * score_esquinas +
            w3 * score_peligro +
            w4 * score_movilidad +
            w5 * score_bordes
        )

    def podaAlphaBeta_eval(self, estado):
        jugador = estado.jugador

        def max_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return self.funcion_evaluacion(e)
            v = -float('inf')
            for accion in self.jugadas(e):
                v = max(v, min_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v >= beta: return v
                alpha = max(alpha, v)
            return v

        def min_value(e, alpha, beta, profundidad):
            if self.testTerminal(e) or profundidad >= self.altura:
                return self.funcion_evaluacion(e)
            v = float('inf')
            for accion in self.jugadas(e):
                v = min(v, max_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v <= alpha: return v
                beta = min(beta, v)
            return v

        mejor_score = -float('inf')
        beta = float('inf')
        mejor_accion = self.jugadas(estado)[0] if self.jugadas(estado) else None
        
        for accion in self.jugadas(estado):
            v = min_value(self.getResultado(estado, accion), mejor_score, beta, 1) # Inicia en profundidad 1
            if v > mejor_score:
                mejor_score = v
                mejor_accion = accion
        return mejor_accion

    def mide_tiempo(funcion):
        def funcion_medida(*args, **kwargs):
            inicio = time.time()
            c = funcion(*args, **kwargs)
            return c
        return funcion_medida

    @mide_tiempo
    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return
        
        self.set_acciones(self.podaAlphaBeta_eval(self.estado))