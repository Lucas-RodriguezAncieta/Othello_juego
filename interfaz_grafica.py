# interfaz_grafica.py
import sys
import pygame
import numpy as np

# Dimensiones generales
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 820
BOARD_SIZE = 8
MARGIN = 30
PANEL_WIDTH = 240
BOARD_PIXELS = WINDOW_HEIGHT - (MARGIN * 2)
CELL_SIZE = BOARD_PIXELS // BOARD_SIZE
BOARD_WIDTH = CELL_SIZE * BOARD_SIZE
BOARD_HEIGHT = CELL_SIZE * BOARD_SIZE
BOARD_X = MARGIN
BOARD_Y = MARGIN
PANEL_X = BOARD_X + BOARD_WIDTH + 24
PANEL_Y = MARGIN
PANEL_HEIGHT = BOARD_HEIGHT

PIECE_RADIUS = CELL_SIZE // 2 - 8
HIGHLIGHT_RADIUS = CELL_SIZE // 2 - 14

# Colores
BG_TOP = (17, 78, 47)
BG_BOTTOM = (10, 47, 29)
BOARD_GREEN = (22, 109, 63)
BOARD_GREEN_ALT = (20, 98, 57)
GRID_COLOR = (11, 54, 31)
BLACK = (20, 20, 20)
WHITE = (245, 245, 245)
GOLD = (231, 196, 71)
RED = (220, 91, 91)
GREEN = (96, 213, 140)
PANEL_BG = (21, 28, 34)
PANEL_BORDER = (68, 84, 96)
TEXT_SOFT = (214, 223, 230)
TEXT_DIM = (160, 173, 184)
MOVE_HINT = (255, 232, 124, 130)
SHADOW = (0, 0, 0, 70)


class InterfazJuego:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Othello IA")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 22)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.big_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)

        self.default_board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        mid = BOARD_SIZE // 2
        self.default_board[mid - 1][mid - 1] = 2
        self.default_board[mid][mid] = 2
        self.default_board[mid - 1][mid] = 1
        self.default_board[mid][mid - 1] = 1

    def draw_waiting_screen(self, status, player_color_info):
        self._draw_background()
        self._draw_board(self.default_board)
        self._draw_panel_base()

        self._draw_center_overlay(
            title="Esperando oponente",
            lines=[
                status or "Conectando al servidor...",
                f"Color asignado: {player_color_info}" if player_color_info else "Aun no se asigno color.",
                "El juego comenzara cuando haya dos jugadores conectados.",
            ],
        )

        self._draw_panel_lines(
            "Estado de conexion",
            [
                status or "Sin estado disponible",
                f"Jugador: {player_color_info}" if player_color_info else "Jugador: pendiente",
                "Modo: espera",
            ],
        )
        pygame.display.flip()

    def draw_game_state(self, game_state, player_color):
        self._draw_background()
        self._draw_panel_base()

        if not game_state:
            self._draw_board(self.default_board)
            self._draw_panel_lines(
                "Sin partida",
                ["No hay estado de juego disponible."],
            )
            pygame.display.flip()
            return

        board = np.array(game_state["board"])
        self._draw_board(board)
        self._draw_coordinates()
        self._draw_pieces(board)

        is_my_turn = game_state["current_player"] == player_color
        if not game_state["game_over"] and is_my_turn:
            self._draw_valid_moves(game_state.get("valid_moves", []))

        self._draw_game_info(game_state, player_color)
        pygame.display.flip()

    def _draw_background(self):
        for y in range(WINDOW_HEIGHT):
            ratio = y / max(WINDOW_HEIGHT - 1, 1)
            r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
            g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
            b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    def _draw_board(self, board):
        shadow = pygame.Surface((BOARD_WIDTH + 10, BOARD_HEIGHT + 10), pygame.SRCALPHA)
        shadow.fill(SHADOW)
        self.screen.blit(shadow, (BOARD_X + 6, BOARD_Y + 8))

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = BOARD_GREEN if (row + col) % 2 == 0 else BOARD_GREEN_ALT
                rect = pygame.Rect(
                    BOARD_X + col * CELL_SIZE,
                    BOARD_Y + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 2)

    def _draw_coordinates(self):
        for index in range(BOARD_SIZE):
            x = BOARD_X + index * CELL_SIZE + CELL_SIZE // 2
            y = BOARD_Y + index * CELL_SIZE + CELL_SIZE // 2

            col_text = self.small_font.render(str(index), True, TEXT_SOFT)
            row_text = self.small_font.render(str(index), True, TEXT_SOFT)

            self.screen.blit(
                col_text,
                (x - col_text.get_width() // 2, BOARD_Y - 24),
            )
            self.screen.blit(
                row_text,
                (BOARD_X - 20, y - row_text.get_height() // 2),
            )

    def _draw_pieces(self, board):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row, col] == 0:
                    continue

                center = (
                    BOARD_X + col * CELL_SIZE + CELL_SIZE // 2,
                    BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2,
                )
                color = BLACK if board[row, col] == 1 else WHITE

                pygame.draw.circle(
                    self.screen,
                    (0, 0, 0, 50),
                    (center[0] + 3, center[1] + 4),
                    PIECE_RADIUS,
                )
                pygame.draw.circle(self.screen, color, center, PIECE_RADIUS)
                pygame.draw.circle(self.screen, GRID_COLOR, center, PIECE_RADIUS, 2)

    def _draw_valid_moves(self, valid_moves):
        for row, col in valid_moves:
            highlight_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                highlight_surface,
                MOVE_HINT,
                (CELL_SIZE // 2, CELL_SIZE // 2),
                HIGHLIGHT_RADIUS,
            )
            self.screen.blit(
                highlight_surface,
                (BOARD_X + col * CELL_SIZE, BOARD_Y + row * CELL_SIZE),
            )

    def _draw_panel_base(self):
        panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel_rect, 2, border_radius=14)

    def _draw_game_info(self, game_state, player_color):
        scores = game_state["scores"]
        is_my_turn = game_state["current_player"] == player_color
        color_name = "Negro" if player_color == 1 else "Blanco"

        if game_state["game_over"]:
            winner = game_state["winner"]
            if winner == 0:
                status = "Empate"
                status_color = GOLD
            elif winner == player_color:
                status = "Ganaste"
                status_color = GREEN
            else:
                status = "Perdiste"
                status_color = RED
        else:
            status = "Tu turno" if is_my_turn else "Turno rival"
            status_color = GREEN if is_my_turn else RED

        valid_moves = len(game_state.get("valid_moves", []))

        self.screen.blit(
            self.title_font.render("Othello", True, WHITE),
            (PANEL_X + 20, PANEL_Y + 18),
        )

        self.screen.blit(
            self.big_font.render(status, True, status_color),
            (PANEL_X + 20, PANEL_Y + 86),
        )

        sections = [
            ("Jugador", [f"Color: {color_name}"]),
            ("Marcador", [f"Negro: {scores['black']}", f"Blanco: {scores['white']}"]),
            (
                "Turno actual",
                [f"Juega: {'Negro' if game_state['current_player'] == 1 else 'Blanco'}"],
            ),
            ("Movidas", [f"Opciones visibles: {valid_moves}"]),
        ]

        y = PANEL_Y + 150
        for title, lines in sections:
            y = self._draw_panel_block(title, lines, y)

        footer = "Haz clic en una casilla valida para jugar."
        if game_state["game_over"]:
            footer = "La partida termino. Cierra la ventana para salir."
        elif not is_my_turn:
            footer = "Espera a que el servidor reciba la jugada rival."

        footer_surface = self.small_font.render(footer, True, TEXT_DIM)
        self.screen.blit(footer_surface, (PANEL_X + 20, PANEL_Y + PANEL_HEIGHT - 36))

    def _draw_panel_lines(self, title, lines):
        self.screen.blit(
            self.title_font.render("Othello", True, WHITE),
            (PANEL_X + 20, PANEL_Y + 18),
        )
        self._draw_panel_block(title, lines, PANEL_Y + 112)

    def _draw_panel_block(self, title, lines, top):
        title_surface = self.font.render(title, True, GOLD)
        self.screen.blit(title_surface, (PANEL_X + 20, top))

        line_y = top + 30
        for line in lines:
            line_surface = self.small_font.render(line, True, TEXT_SOFT)
            self.screen.blit(line_surface, (PANEL_X + 20, line_y))
            line_y += 24

        return line_y + 12

    def _draw_center_overlay(self, title, lines):
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        self.screen.blit(overlay, (BOARD_X, BOARD_Y))

        title_surface = self.big_font.render(title, True, WHITE)
        self.screen.blit(
            title_surface,
            (
                BOARD_X + BOARD_WIDTH // 2 - title_surface.get_width() // 2,
                BOARD_Y + 180,
            ),
        )

        y = BOARD_Y + 250
        for line in lines:
            text_surface = self.font.render(line, True, TEXT_SOFT)
            self.screen.blit(
                text_surface,
                (
                    BOARD_X + BOARD_WIDTH // 2 - text_surface.get_width() // 2,
                    y,
                ),
            )
            y += 42

    def get_clicked_cell(self, pos):
        x, y = pos
        if not (
            BOARD_X <= x < BOARD_X + BOARD_WIDTH
            and BOARD_Y <= y < BOARD_Y + BOARD_HEIGHT
        ):
            return None, None

        col = (x - BOARD_X) // CELL_SIZE
        row = (y - BOARD_Y) // CELL_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return int(row), int(col)
        return None, None

    def run_event_loop(self, on_click=None, on_quit=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if on_quit:
                    on_quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if on_click:
                    on_click(event.pos)
        return True

    def quit(self):
        pygame.quit()
        sys.exit()
