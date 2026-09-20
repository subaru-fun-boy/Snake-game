#!/usr/bin/env python3
"""Classic Snake game for the terminal, built with curses.

Controls:
    Arrow keys - move
    p          - pause / resume
    q          - quit
    r          - restart (after game over)
"""

import curses
import random

DELAY_MS = 100

KEY_DIRECTIONS = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
}

OPPOSITES = {
    (-1, 0): (1, 0),
    (1, 0): (-1, 0),
    (0, -1): (0, 1),
    (0, 1): (0, -1),
}


def place_food(snake, height, width):
    while True:
        food = (random.randint(1, height - 2), random.randint(1, width - 2))
        if food not in snake:
            return food


def draw_board(stdscr, snake, food, score, height, width, paused=False):
    stdscr.erase()
    stdscr.border()

    for y, x in snake:
        stdscr.addch(y, x, curses.ACS_CKBOARD)
    stdscr.addch(food[0], food[1], curses.ACS_DIAMOND)

    stdscr.addstr(0, 2, f" Score: {score} ")

    if paused:
        msg = "PAUSED - press 'p' to resume"
        stdscr.addstr(height // 2, max(1, (width - len(msg)) // 2), msg)

    stdscr.refresh()


def show_game_over(stdscr, score, height, width):
    """Display the game-over screen and block for 'r' (restart) or 'q' (quit)."""
    stdscr.nodelay(False)
    lines = [
        "GAME OVER",
        f"Final score: {score}",
        "Press 'r' to restart or 'q' to quit",
    ]
    stdscr.erase()
    stdscr.border()
    for i, line in enumerate(lines):
        stdscr.addstr(height // 2 - 1 + i, max(1, (width - len(line)) // 2), line)
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord("r"), ord("R")):
            return True
        if key in (ord("q"), ord("Q")):
            return False


def run_game(stdscr, height, width):
    """Play one round. Returns the final score."""
    stdscr.nodelay(True)
    stdscr.timeout(DELAY_MS)
    stdscr.keypad(True)

    mid_y, mid_x = height // 2, width // 2
    snake = [(mid_y, mid_x), (mid_y, mid_x - 1), (mid_y, mid_x - 2)]
    direction = (0, 1)
    food = place_food(snake, height, width)
    score = 0
    paused = False

    while True:
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            return score, True
        if key in (ord("p"), ord("P")):
            paused = not paused
        elif key in KEY_DIRECTIONS and not paused:
            new_direction = KEY_DIRECTIONS[key]
            if OPPOSITES[new_direction] != direction:
                direction = new_direction

        if paused:
            draw_board(stdscr, snake, food, score, height, width, paused=True)
            continue

        head_y, head_x = snake[0]
        new_head = (head_y + direction[0], head_x + direction[1])

        hit_wall = (
            new_head[0] <= 0
            or new_head[0] >= height - 1
            or new_head[1] <= 0
            or new_head[1] >= width - 1
        )
        will_grow = new_head == food
        # The tail cell vacates this move unless the snake is growing, so it
        # must not count as an obstacle in that case.
        body_to_check = snake if will_grow else snake[:-1]
        if hit_wall or new_head in body_to_check:
            return score, False

        snake.insert(0, new_head)

        if will_grow:
            score += 10
            food = place_food(snake, height, width)
        else:
            snake.pop()

        draw_board(stdscr, snake, food, score, height, width)


def main(stdscr):
    curses.curs_set(0)
    term_height, term_width = stdscr.getmaxyx()
    height, width = min(term_height, 30), min(term_width, 60)

    while True:
        score, quit_requested = run_game(stdscr, height, width)
        if quit_requested:
            return
        if not show_game_over(stdscr, score, height, width):
            return


if __name__ == "__main__":
    curses.wrapper(main)
