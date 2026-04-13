from AgenteIA.AgenteJugador import AgenteJugador
import random

class AgenteAleatorio(AgenteJugador):

    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return
        
        mov = random.choice(self.estado.movidas)
        self.set_acciones(mov)