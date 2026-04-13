from AgenteIA.Agente import Agente
from collections import namedtuple
import time
import numpy as np

ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')

class AgenteJugador(Agente):
    def __init__(self, altura=3):
        Agente.__init__(self)
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta" # Por defecto

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
        from TableroOthello import TableroOthello
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
        import numpy as np
        from TableroOthello import TableroOthello

        tablero = estado.tablero
        jugador = estado.jugador
        rival = 3 - jugador
        size = len(tablero)

        # -----------------------------
        # 1. Diferencia de fichas
        # -----------------------------
        fichas_jugador = np.sum(tablero == jugador)
        fichas_rival = np.sum(tablero == rival)
        score_fichas = fichas_jugador - fichas_rival

        # -----------------------------
        # 2. Esquinas (MUY importantes)
        # -----------------------------
        esquinas = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
        score_esquinas = 0
        for (r, c) in esquinas:
            if tablero[r][c] == jugador:
                score_esquinas += 1
            elif tablero[r][c] == rival:
                score_esquinas -= 1

        # -----------------------------
        # 3. Casillas peligrosas (alrededor de esquinas)
        # -----------------------------
        peligrosas = [
            (0,1),(1,0),(1,1),
            (0,size-2),(1,size-1),(1,size-2),
            (size-2,0),(size-1,1),(size-2,1),
            (size-2,size-1),(size-1,size-2),(size-2,size-2)
        ]

        score_peligro = 0
        for (r,c) in peligrosas:
            if tablero[r][c] == jugador:
                score_peligro -= 1
            elif tablero[r][c] == rival:
                score_peligro += 1

        # -----------------------------
        # 4. Movilidad (clave)
        # -----------------------------
        mis_movidas = len(estado.movidas)

        temp = TableroOthello(size)
        mov_rival = len(temp._get_valid_moves(tablero, rival))

        score_movilidad = mis_movidas - mov_rival

        # -----------------------------
        # 5. Bordes (sin esquinas)
        # -----------------------------
        score_bordes = 0
        for i in range(size):
            for j in range(size):
                if (i,j) in esquinas:
                    continue
                if i == 0 or i == size-1 or j == 0 or j == size-1:
                    if tablero[i][j] == jugador:
                        score_bordes += 1
                    elif tablero[i][j] == rival:
                        score_bordes -= 1

        # -----------------------------
        # SCORE FINAL (mejorado)
        # -----------------------------
        return (
            2 * score_fichas +
            100 * score_esquinas +
            -30 * score_peligro +
            10 * score_movilidad +
            5 * score_bordes
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