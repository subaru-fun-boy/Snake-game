#!/usr/bin/env python3
"""Classic Snake game for the terminal, built with curses.

Controls:
    Arrow keys - move
    p          - pause / resume
    q          - quit
    r          - restart (after game over)
"""

import curses
import logging
import os
import random

DELAY_MS = 100

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake_debug.log")

logging.basicConfig(
    filename=LOG_PATH,
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("snake")

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
    try:
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
    except curses.error:
        log.exception(
            "curses draw error: snake=%s food=%s score=%s height=%s width=%s",
            snake, food, score, height, width,
        )
        raise


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
    tick = 0

    log.info(
        "round start: board=%sx%s snake=%s direction=%s food=%s",
        height, width, snake, direction, food,
    )

    while True:
        tick += 1
        key = stdscr.getch()
        if key != -1:
            log.debug("tick=%d key=%r", tick, key)

        if key in (ord("q"), ord("Q")):
            log.info("tick=%d quit key pressed, score=%d", tick, score)
            return score, True
        if key in (ord("p"), ord("P")):
            paused = not paused
            log.info("tick=%d paused=%s", tick, paused)
        elif key in KEY_DIRECTIONS and not paused:
            new_direction = KEY_DIRECTIONS[key]
            if OPPOSITES[new_direction] != direction:
                log.debug("tick=%d direction change %s -> %s", tick, direction, new_direction)
                direction = new_direction
            else:
                log.debug("tick=%d rejected reverse direction %s", tick, new_direction)

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
        collided = new_head in body_to_check
        if hit_wall or collided:
            log.warning(
                "tick=%d GAME OVER: head=%s new_head=%s hit_wall=%s collided=%s "
                "snake=%s score=%d",
                tick, snake[0], new_head, hit_wall, collided, snake, score,
            )
            return score, False

        snake.insert(0, new_head)

        if will_grow:
            score += 10
            food = place_food(snake, height, width)
            log.debug("tick=%d ate food, new score=%d, new food=%s", tick, score, food)
        else:
            snake.pop()

        draw_board(stdscr, snake, food, score, height, width)


def main(stdscr):
    curses.curs_set(0)
    term_height, term_width = stdscr.getmaxyx()
    height, width = min(term_height, 30), min(term_width, 60)
    log.info(
        "session start: terminal=%sx%s board=%sx%s delay_ms=%d",
        term_height, term_width, height, width, DELAY_MS,
    )

    while True:
        score, quit_requested = run_game(stdscr, height, width)
        if quit_requested:
            return
        if not show_game_over(stdscr, score, height, width):
            log.info("quit from game-over screen, score=%d", score)
            return
        log.info("restart requested from game-over screen, previous score=%d", score)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception:
        log.exception("unhandled exception - game crashed")
        raise
    finally:
        log.info("program exiting, log at %s", LOG_PATH)
