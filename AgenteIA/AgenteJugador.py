from AgenteIA.Agente import Agente
from collections import namedtuple
import time

ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')

class AgenteJugador(Agente):
    def __init__(self, altura=3):
        Agente.__init__(self)
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta" # Por defecto

    def jugadas(self, estado):
        raise NotImplementedError

    def get_utilidad(self, estado, jugador):
        raise NotImplementedError

    def testTerminal(self, estado):
        return not estado.movidas

    def getResultado(self, estado, m):
        raise NotImplementedError

    def funcion_evaluacion(self, estado):
        tablero = estado.tablero
        jugador = estado.jugador
        rival = 3 - jugador
        size = len(tablero)

        # -----------------------------
        # 1. Conteo de fichas
        # -----------------------------
        fichas_jugador = (tablero == jugador).sum()
        fichas_rival = (tablero == rival).sum()
        score_fichas = fichas_jugador - fichas_rival

        # -----------------------------
        # 2. Esquinas
        # -----------------------------
        esquinas = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
        score_esquinas = 0

        for (r, c) in esquinas:
            if tablero[r][c] == jugador:
                score_esquinas += 1
            elif tablero[r][c] == rival:
                score_esquinas -= 1

        # -----------------------------
        # 3. Bordes (SIN esquinas)
        # -----------------------------
        score_bordes = 0

        for i in range(size):
            for j in range(size):
                if (i, j) in esquinas:
                    continue

                if i == 0 or i == size-1 or j == 0 or j == size-1:
                    if tablero[i][j] == jugador:
                        score_bordes += 1
                    elif tablero[i][j] == rival:
                        score_bordes -= 1

        # -----------------------------
        # 4. Movilidad (BIEN HECHA)
        # -----------------------------
        mis_movidas = len(estado.movidas)

        from TableroOthello import TableroOthello
        temp = TableroOthello(size)
        mov_rival = len(temp._get_valid_moves(tablero, rival))

        score_movilidad = mis_movidas - mov_rival

        # -----------------------------
        # SCORE FINAL (pesos equilibrados)
        # -----------------------------
        return (
            1 * score_fichas +
            20 * score_esquinas +
            3 * score_bordes +
            5 * score_movilidad
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