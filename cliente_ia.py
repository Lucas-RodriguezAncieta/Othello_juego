from cliente_base import ClienteBase
from interfaz_grafica import InterfazJuego
from AgenteIA.AgenteJugador import AgenteJugador
from Estado import ElEstado
import numpy as np
import time


class ClienteIA(ClienteBase):

    def __init__(self, host, port):
        super().__init__(host, port)

        self.ui = InterfazJuego()
        self.running = True

        # 🔥 IA
        self.ia = AgenteJugador(altura=4)

        # 🔥 evita doble turno
        self.ultimo_turno = None

        # 🔥 callback
        self.on_message_received = self.procesar_mensaje

    # 🧠 IA reacciona a mensajes
    def procesar_mensaje(self, message):

        msg_type = message.get("type")

        if msg_type in ["game_start", "game_update"]:

            if not self.game_state:
                return

            if self.game_state["game_over"]:
                print("🏁 Juego terminado")
                return

            turno_actual = self.game_state["current_player"]

            # ❌ no es mi turno
            if turno_actual != self.player_color:
                return

            # ❌ evitar repetir turno
            if turno_actual == self.ultimo_turno:
                return

            self.ultimo_turno = turno_actual

            print("🧠 IA pensando...")

            tablero = np.array(self.game_state["board"])
            movidas = self.game_state["valid_moves"]

            estado = ElEstado(
                jugador=self.player_color,
                tablero=tablero,
                movidas=movidas,
                get_utilidad=0
            )

            self.ia.estado = estado
            self.ia.programa()

            accion = self.ia.get_acciones()

            if not accion:
                print("⚠️ IA no encontró jugada")
                return

            valid_moves = [tuple(m) for m in movidas]

            # ✔ validar jugada
            if accion in valid_moves:
                row, col = accion
            else:
                print("⚠️ IA intentó jugada inválida, usando alternativa")
                if valid_moves:
                    row, col = valid_moves[0]
                else:
                    return

            # 🔥 delay corto (rápido pero estable)
            time.sleep(0.1)

            print(f"🚀 Jugando: ({row}, {col})")
            self.send_move(row, col)

    # 🔴 cerrar
    def on_quit(self):
        self.running = False
        self.disconnect("Usuario cerró la ventana")

    # 🎮 loop principal
    def run(self):
        self.connect()

        while self.running:

            if not self.ui.run_event_loop(on_quit=self.on_quit):
                break

            if not self.connected or self.waiting_for_opponent:
                color_info = (
                    "Negro" if self.player_color == 1 else "Blanco"
                ) if self.player_color else ""
                self.ui.draw_waiting_screen(self.connection_status, color_info)
            else:
                self.ui.draw_game_state(self.game_state, self.player_color)

            self.ui.clock.tick(30)

        self.ui.quit()


# 🔥 MAIN (IMPORTANTE)
if __name__ == "__main__":
    host = input("Servidor [localhost]: ").strip() or 'localhost'
    port_input = input("Puerto [5555]: ").strip()
    port = int(port_input) if port_input.isdigit() else 5555

    cliente = ClienteIA(host, port)
    cliente.run()