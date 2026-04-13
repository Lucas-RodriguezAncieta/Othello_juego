import random
import numpy as np
from AgenteIA.AgenteJugador import AgenteJugador
from TableroOthello import TableroOthello
from AgenteIA.AgenteAleatorio import AgenteAleatorio

class Genetico:

    def __init__(self, poblacion_size=6, generaciones=5):
        self.poblacion_size = poblacion_size
        self.generaciones = generaciones

    # -------------------------
    # Crear individuo
    # -------------------------
    def crear_individuo(self):
        return [random.uniform(-50, 150) for _ in range(5)]

    # -------------------------
    # Fitness REAL
    # -------------------------
    def fitness(self, pesos):
        victorias = 0
        partidas = 3

        for _ in range(partidas):
            tablero = TableroOthello()

            ia = AgenteJugador(altura=3)
            ia.pesos = pesos

            rival = AgenteAleatorio()

            tablero.insertar(ia)
            tablero.insertar(rival)

            tablero.run()

            # evaluar resultado
            t = tablero.juegoActual.tablero
            negras = np.sum(t == 1)
            blancas = np.sum(t == 2)

            if negras > blancas:
                victorias += 1

        return victorias / partidas

    # -------------------------
    # Selección por torneo
    # -------------------------
    def torneo(self, poblacion, scores, k=3):
        participantes = random.sample(list(zip(poblacion, scores)), k)
        return max(participantes, key=lambda x: x[1])[0]

    # -------------------------
    # Cruce aritmético
    # -------------------------
    def cruce(self, p1, p2):
        alpha = random.random()
        return [
            alpha * x + (1 - alpha) * y
            for x, y in zip(p1, p2)
        ]

    # -------------------------
    # Mutación gaussiana
    # -------------------------
    def mutar(self, individuo, prob=0.3, sigma=5):
        for i in range(len(individuo)):
            if random.random() < prob:
                individuo[i] += random.gauss(0, sigma)
        return individuo

    # -------------------------
    # Evolución
    # -------------------------
    def evolucionar(self):

        poblacion = [self.crear_individuo() for _ in range(self.poblacion_size)]

        for g in range(self.generaciones):
            print(f"\n===== Generación {g} =====")

            scores = [self.fitness(ind) for ind in poblacion]
            print(f" Mejor fitness generación {g}: {max(scores)}")  
            for i, (ind, sc) in enumerate(zip(poblacion, scores)):
                print(f"Ind {i}: {ind} -> {sc}")

            nueva_poblacion = []

            # elitismo (guardar el mejor)
            mejor = poblacion[np.argmax(scores)]
            nueva_poblacion.append(mejor)

            while len(nueva_poblacion) < self.poblacion_size:
                p1 = self.torneo(poblacion, scores)
                p2 = self.torneo(poblacion, scores)

                hijo = self.cruce(p1, p2)
                hijo = self.mutar(hijo)

                nueva_poblacion.append(hijo)

            poblacion = nueva_poblacion

        # mejor final
        scores = [self.fitness(ind) for ind in poblacion]
        mejor = poblacion[np.argmax(scores)]

        return mejor