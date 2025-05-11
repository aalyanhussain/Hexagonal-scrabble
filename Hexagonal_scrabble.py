import pygame
import numpy as np
import random
import nltk
from nltk.corpus import words
from pygame import freetype

nltk.download('words')
with open("sowpods.txt") as f:
    ENGLISH_WORDS = set(line.strip().lower() for line in f if len(line.strip()) >= 3)

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
HEX_SIZE = 40
BOARD_RADIUS = 5

# Colors
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GRAY = (170, 170, 170)
RED = (220, 50, 50)
BLUE = (50, 100, 255)
GREEN = (30, 180, 90)
LIGHT_RED = (255, 180, 180)
LIGHT_BLUE = (180, 210, 255)
BG_COLOR = (230, 240, 255)

# Fonts
freetype.init()
font = freetype.SysFont("Arial", 24)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hexagonal Scrabble")

# Hex grid math

def hex_to_pixel(q, r):
    x = WIDTH // 2 + HEX_SIZE * (3/2 * q)
    y = HEIGHT // 2 + HEX_SIZE * (np.sqrt(3) * (r + q/2))
    return x, y

def hexagon_points(x, y, size):
    return [(x + size * np.cos(np.pi / 3 * i), y + size * np.sin(np.pi / 3 * i)) for i in range(6)]

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]

# Game state
board = {(q, r): None for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1) for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1) if abs(q + r) <= BOARD_RADIUS}
player_score = ai_score = 0
current_input = ""
selected_cell = None
validated_words = set()
player_rack = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8)]
last_scored_paths = []

# Core functions

def draw_board():
    screen.fill(BG_COLOR)
    for (q, r), tile in board.items():
        x, y = hex_to_pixel(q, r)
        poly = hexagon_points(x, y, HEX_SIZE)

        for path, owner in last_scored_paths:
            if (q, r) in path:
                pygame.draw.polygon(screen, LIGHT_RED if owner == "player" else LIGHT_BLUE, poly)

        pygame.draw.polygon(screen, GRAY, poly, 2)

        if tile:
            letter, owner = tile
            color = RED if owner == "player" else BLUE
            font.render_to(screen, (x - 10, y - 12), letter, color)

    if selected_cell:
        x, y = hex_to_pixel(*selected_cell)
        pygame.draw.polygon(screen, GREEN, hexagon_points(x, y, HEX_SIZE), 3)

    font.render_to(screen, (20, 20), f"Player: {player_score}   AI: {ai_score}", BLACK)
    font.render_to(screen, (20, 60), f"Letter: {current_input.upper()}", BLACK)
    font.render_to(screen, (20, HEIGHT - 40), "Rack: " + ' '.join(player_rack), BLACK)

def place_letter(q, r, letter, player):
    if board[(q, r)] is None:
        board[(q, r)] = (letter.upper(), player)
        return True
    return False

def collect_words():
    words_found = []
    for (q, r), tile in board.items():
        if tile:
            for dq, dr in DIRECTIONS:
                word = tile[0]
                path = [(q, r)]
                for i in range(1, 6):
                    pos = (q + dq * i, r + dr * i)
                    if pos in board and board[pos]:
                        word += board[pos][0]
                        path.append(pos)
                    else:
                        break
                    if len(word) >= 3 and word.lower() in ENGLISH_WORDS:
                        words_found.append((word.lower(), path))
    return words_found

def update_scores(current_player):
    global player_score, ai_score, last_scored_paths
    new_words = collect_words()
    last_scored_paths = []
    for word, path in new_words:
        if word not in validated_words:
            validated_words.add(word)
            owner = board[path[-1]][1]
            if owner == current_player:
                if owner == "player":
                    player_score += 5
                else:
                    ai_score += 5
                last_scored_paths.append((path, owner))

def ai_play():
    available = [pos for pos in board if board[pos] is None]
    for (q, r), tile in board.items():
        if tile and tile[1] == "player":
            for dq, dr in DIRECTIONS:
                word = tile[0]
                path = [(q, r)]
                for i in range(1, 6):
                    pos = (q + dq * i, r + dr * i)
                    if pos in board:
                        if board[pos]:
                            word += board[pos][0]
                            path.append(pos)
                        elif pos in available:
                            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                                if len(word + letter) >= 3 and (word + letter).lower() in ENGLISH_WORDS:
                                    if place_letter(pos[0], pos[1], letter, "ai"):
                                        update_scores("ai")
                                        return
                            break
                    else:
                        break
    random.shuffle(available)
    place_letter(*available[0], random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), "ai")
    update_scores("ai")

def refill_rack():
    while len(player_rack) < 8:
        player_rack.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

def check_winner():
    if player_score >= 150 and ai_score >= 150:
        return "It's a tie!"
    elif player_score >= 150:
        return "Player wins!"
    elif ai_score >= 150:
        return "AI wins!"
    return None

def show_winner_message(message):
    screen.fill(WHITE)
    text_rect = font.get_rect(message)
    font.render_to(screen, (WIDTH//2 - text_rect[2]//2, HEIGHT//2 - text_rect[3]//2), message, BLACK)
    pygame.display.flip()
    pygame.time.delay(5000)

# Game loop
running = True
player_turn = True
clock = pygame.time.Clock()

while running:
    draw_board()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            for (q, r) in board:
                hx, hy = hex_to_pixel(q, r)
                if np.hypot(hx - x, hy - y) < HEX_SIZE:
                    selected_cell = (q, r)
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and player_turn and selected_cell:
                if current_input.isalpha() and len(current_input) == 1 and current_input.upper() in player_rack:
                    if place_letter(*selected_cell, current_input, "player"):
                        player_rack.remove(current_input.upper())
                        refill_rack()
                        update_scores("player")
                        if winner := check_winner():
                            show_winner_message(winner)
                            running = False
                        else:
                            player_turn = False
                            ai_play()
                            if winner := check_winner():
                                show_winner_message(winner)
                                running = False
                            else:
                                player_turn = True
                current_input = ""
            elif event.key == pygame.K_BACKSPACE:
                current_input = current_input[:-1]
            elif event.unicode.isalpha():
                current_input += event.unicode

    clock.tick(30)

pygame.quit()
