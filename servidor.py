import socket
import threading
import json
import numpy as np
import time
import traceback
from Estado import ElEstado
from AgenteIA.AgenteJugador import AgenteJugador


class GameServer:
    def __init__(self, host='127.0.0.1', port=5555, vs_ai=False, ai_depth=4):
        self.host = host
        self.port = port
        self.vs_ai = vs_ai
        self.ai_depth = ai_depth
        self.ai_color = 2
        self.human_color = 1
        self.server_socket = None
        self.clients = []
        self.client_info = []
        self.running = False
        self.lock = threading.Lock()
        self.ai_agent = AgenteJugador(altura=ai_depth) if vs_ai else None
        self.reset_game()

    def reset_game(self):
        self.board = np.zeros((8, 8), dtype=int)
        mid = 4
        self.board[mid - 1][mid - 1] = 2
        self.board[mid][mid] = 2
        self.board[mid - 1][mid] = 1
        self.board[mid][mid - 1] = 1
        self.current_player = 1
        self.game_over = False
        self.winner = None
        print("🎮 Juego reiniciado")

    def get_valid_moves(self, player=None):
        if player is None:
            player = self.current_player
        valid_moves = []
        for row in range(8):
            for col in range(8):
                if self.is_valid_move(row, col, player):
                    valid_moves.append((row, col))
        return valid_moves

    def is_valid_move(self, row, col, player):
        if self.board[row][col] != 0:
            return False
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent = 3 - player
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False
            while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == opponent:
                found_opponent = True
                r += dr
                c += dc
            if found_opponent and 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == player:
                return True
        return False

    def make_move(self, row, col, player):
        if player != self.current_player:
            return False, "No es tu turno"
        if not self.is_valid_move(row, col, player):
            return False, "Movimiento inválido"

        self.board[row][col] = player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent = 3 - player
        flipped = 0

        for dr, dc in directions:
            r, c = row + dr, col + dc
            to_flip = []
            while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == opponent:
                to_flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == player:
                for flip_row, flip_col in to_flip:
                    self.board[flip_row][flip_col] = player
                    flipped += 1

        self.current_player = 3 - self.current_player
        if not self.get_valid_moves():
            self.current_player = 3 - self.current_player
            if not self.get_valid_moves():
                self.game_over = True
                self.determine_winner()
        return True, "Movimiento exitoso"

    def determine_winner(self):
        black_count = np.sum(self.board == 1)
        white_count = np.sum(self.board == 2)
        if black_count > white_count:
            self.winner = 1
        elif white_count > black_count:
            self.winner = 2
        else:
            self.winner = 0

    def get_game_state(self):
        board_list = self.board.tolist()
        valid_moves = self.get_valid_moves()
        black_score = int(np.sum(self.board == 1))
        white_score = int(np.sum(self.board == 2))

        return {
            'board': board_list,
            'current_player': int(self.current_player),
            'game_over': bool(self.game_over),
            'winner': int(self.winner) if self.winner is not None else None,
            'valid_moves': [(int(row), int(col)) for row, col in valid_moves],
            'mode': 'human_vs_ai' if self.vs_ai else 'human_vs_human',
            'scores': {
                'black': black_score,
                'white': white_score
            }
        }

    def send_to_client(self, client_socket, message):
        try:
            # Función personalizada para serializar tipos numpy
            def numpy_serializer(obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (np.bool_)):
                    return bool(obj)
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            message_str = json.dumps(message, default=numpy_serializer) + '\n'
            client_socket.send(message_str.encode('utf-8'))
            print(f"📤 Enviado a cliente: {message['type']}")
            return True
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            traceback.print_exc()
            return False

    def broadcast_to_all(self, message):
        with self.lock:
            clients_to_remove = []
            for i, client_socket in enumerate(self.clients):
                if client_socket:
                    if not self.send_to_client(client_socket, message):
                        print(f"⚠️ Cliente {i} desconectado")
                        clients_to_remove.append(i)

            # Remover clientes desconectados
            for i in sorted(clients_to_remove, reverse=True):
                if i < len(self.clients):
                    self.clients[i] = None
                    self.client_info[i] = None

    def handle_client(self, client_socket, client_address, client_id):
        print(f"👤 Cliente {client_id} conectado desde {client_address}")

        try:
            player_color = self.human_color if self.vs_ai else client_id + 1

            with self.lock:
                while len(self.clients) <= client_id:
                    self.clients.append(None)
                while len(self.client_info) <= client_id:
                    self.client_info.append(None)

                self.clients[client_id] = client_socket
                self.client_info[client_id] = {
                    'address': client_address,
                    'color': player_color,
                    'connected': True
                }

            print(
                f"✅ Cliente {client_id} registrado en lista. Total: {sum(1 for c in self.clients if c is not None)}/2")

            welcome_msg = {
                'type': 'welcome',
                'player_color': int(player_color),
                'message': f'Eres el jugador {"Negro" if player_color == 1 else "Blanco"}',
                'client_id': int(client_id)
            }
            self.send_to_client(client_socket, welcome_msg)

            time.sleep(0.3)

            with self.lock:
                active_count = sum(1 for c in self.clients if c is not None)

            print(f"📊 Estado actual: {active_count}/2 jugadores activos")

            if self.vs_ai:
                print("🤖 Modo IA activo, iniciando partida contra la computadora...")
                time.sleep(0.3)
                self.start_game_if_ready()
            elif active_count == 2:
                print("🚀 Ambos jugadores conectados, iniciando juego...")
                time.sleep(0.5)
                self.start_game_if_ready()
            else:
                wait_msg = {
                    'type': 'waiting',
                    'message': f'Esperando oponente... ({active_count}/2 jugadores)'
                }
                self.send_to_client(client_socket, wait_msg)
                print(f"⏳ Cliente {client_id} en modo espera ({active_count}/2)")

            buffer = ""
            while self.running:
                try:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        print(f"📭 Cliente {client_id} cerró la conexión")
                        break

                    buffer += data
                    while '\n' in buffer:
                        message_str, buffer = buffer.split('\n', 1)
                        if message_str.strip():
                            try:
                                message = json.loads(message_str)
                                print(f"📨 Mensaje de cliente {client_id}: {message['type']}")
                                self.process_client_message(client_socket, client_id, player_color, message)
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON inválido de cliente {client_id}: {e}")

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error recibiendo datos de cliente {client_id}: {e}")
                    break

        except Exception as e:
            print(f"❌ Error con cliente {client_id}: {e}")
            traceback.print_exc()
        finally:
            print(f"👋 Cliente {client_id} desconectado")
            with self.lock:
                if client_id < len(self.clients):
                    self.clients[client_id] = None
                if client_id < len(self.client_info):
                    self.client_info[client_id] = {'connected': False}

            try:
                client_socket.close()
            except:
                pass

            disconnect_msg = {
                'type': 'opponent_disconnected',
                'message': 'El oponente se ha desconectado'
            }
            self.broadcast_to_all(disconnect_msg)

    def build_ai_state(self):
        return ElEstado(
            jugador=int(self.current_player),
            tablero=np.copy(self.board),
            movidas=self.get_valid_moves(self.current_player),
            get_utilidad=0
        )

    def maybe_run_ai_turn(self):
        if not self.vs_ai or self.game_over:
            return

        while self.running and not self.game_over and self.current_player == self.ai_color:
            estado = self.build_ai_state()
            if not estado.movidas:
                print("🤖 La IA no tiene movimientos disponibles.")
                break

            self.ai_agent.estado = estado
            self.ai_agent.programa()
            move = self.ai_agent.get_acciones()

            if move is None:
                print("🤖 La IA no seleccionó movimiento.")
                break

            row, col = move
            print(f"🤖 IA juega en ({row}, {col})")
            success, msg = self.make_move(row, col, self.ai_color)
            print(f"🤖 Resultado IA: {msg}")

            if not success:
                break

            update_msg = {
                'type': 'game_update',
                'game_state': self.get_game_state(),
                'message': f'La IA jugó en ({row}, {col})'
            }
            self.broadcast_to_all(update_msg)
            time.sleep(0.35)

    def process_client_message(self, client_socket, client_id, player_color, message):
        msg_type = message.get('type')

        if msg_type == 'move':
            row, col = message.get('row'), message.get('col')
            if row is not None and col is not None:
                print(f"🎯 Cliente {client_id} intenta mover a ({row}, {col})")
                success, msg = self.make_move(row, col, player_color)
                response = {'type': 'move_response', 'success': success, 'message': msg}
                self.send_to_client(client_socket, response)
                if success:
                    print("✅ Movimiento exitoso, actualizando juego...")
                    update_msg = {'type': 'game_update', 'game_state': self.get_game_state()}
                    self.broadcast_to_all(update_msg)
                    self.maybe_run_ai_turn()

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)

            self.running = True
            print(f"🎮 Servidor Othello iniciado en {self.host}:{self.port}")
            print("📍 Esperando jugadores...")

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_socket.settimeout(1)

                    print(f"🔗 Nueva conexión de {client_address}")

                    if self.vs_ai:
                        with self.lock:
                            active_count = sum(1 for c in self.clients if c is not None)
                        if active_count >= 1:
                            reject_message = {
                                'type': 'server_full',
                                'message': 'Este servidor está en modo contra IA y ya tiene un jugador conectado.'
                            }
                            self.send_to_client(client_socket, reject_message)
                            client_socket.close()
                            print("⚠️ Conexión rechazada: el modo vs IA admite solo un jugador humano.")
                            continue

                    with self.lock:
                        slot_index = None
                        for i in range(len(self.clients)):
                            if self.clients[i] is None:
                                slot_index = i
                                break

                        if slot_index is None:
                            slot_index = len(self.clients)
                            self.clients.append(None)
                            self.client_info.append(None)

                        print(f"🆔 Asignando slot {slot_index} al nuevo cliente")
                        self.clients[slot_index] = client_socket

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address, slot_index),
                        name=f"ClientThread-{slot_index}"
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    print(
                        f"✅ Hilo del cliente {slot_index} iniciado. Total activos: {sum(1 for c in self.clients if c is not None)}/2")

                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    print("\n🛑 Deteniendo servidor...")
                    self.running = False
                except Exception as e:
                    print(f"❌ Error aceptando conexión: {e}")

        except Exception as e:
            print(f"❌ Error del servidor: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients:
            if client:
                try:
                    client.close()
                except:
                    pass
        print("🛑 Servidor detenido")

    def start_game_if_ready(self):
        with self.lock:
            active_clients = [c for c in self.clients if c is not None]

        expected_players = 1 if self.vs_ai else 2
        print(f"🔍 Verificando jugadores: {len(active_clients)}/{expected_players} conectados")

        if len(active_clients) == expected_players:
            print("🎉 Jugadores listos. Iniciando juego...")
            self.reset_game()

            game_state = self.get_game_state()
            start_message = {
                'type': 'game_start',
                'game_state': game_state,
                'message': '¡La partida ha comenzado!'
            }

            print("📋 Estado del juego preparado para enviar:")
            print(f"   - Tablero: {len(game_state['board'])}x{len(game_state['board'][0])}")
            print(f"   - Jugador actual: {game_state['current_player']}")
            print(f"   - Movimientos válidos: {len(game_state['valid_moves'])}")
            print(f"   - Puntuación: Negro {game_state['scores']['black']}, Blanco {game_state['scores']['white']}")

            self.broadcast_to_all(start_message)
            print("✅ Mensaje de inicio enviado a los clientes activos")
            self.maybe_run_ai_turn()
            return True

        print(f"⚠️ No hay suficientes jugadores: {len(active_clients)}/{expected_players}")
        return False


if __name__ == "__main__":
    print("=== 🎮 SERVIDOR OTHELLO ===")
    host = input("🌐 Host [127.0.0.1]: ").strip() or '127.0.0.1'
    port_input = input("🔌 Puerto [5555]: ").strip()
    port = int(port_input) if port_input.isdigit() else 5555
    mode_input = input("🤖 ¿Jugar contra IA? [s/N]: ").strip().lower()
    vs_ai = mode_input in {"s", "si", "sí", "y", "yes"}
    ai_depth = 4
    if vs_ai:
        depth_input = input("🧠 Profundidad IA [4]: ").strip()
        ai_depth = int(depth_input) if depth_input.isdigit() and int(depth_input) > 0 else 4

    server = GameServer(host, port, vs_ai=vs_ai, ai_depth=ai_depth)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n⏹️  Servidor interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
