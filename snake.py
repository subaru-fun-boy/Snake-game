#!/usr/bin/env python3
"""Classic Snake game for the terminal, built with curses.

Controls:
    Arrow keys - move
    p          - pause / resume
    q          - quit
    r          - restart (after game over)

Every FRUITS_PER_POOP fruits digested, the snake leaves a permanent
"poop" obstacle behind - crashing into one ends the game just like
hitting a wall or your own body.
"""

import curses
import logging
import os
import random

DELAY_MS = 100
POOP_CHAR = ord("%")
CRASH_CHAR = ord("X")
FRUITS_PER_POOP = 5

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


def place_food(snake, poop, height, width):
    while True:
        food = (random.randint(1, height - 2), random.randint(1, width - 2))
        if food not in snake and food not in poop:
            return food


def draw_board(win, snake, poop, food, score, height, width, paused=False, crash=None):
    try:
        win.erase()
        win.border()

        for y, x in poop:
            win.addch(y, x, POOP_CHAR)

        for y, x in snake:
            win.addch(y, x, curses.ACS_CKBOARD)
        win.addch(food[0], food[1], curses.ACS_DIAMOND)

        if crash is not None:
            # The crash cell can land on the border itself (a wall hit), and
            # curses refuses a plain addch at the window's absolute bottom-
            # right corner, so failing to draw the marker there is fine.
            try:
                win.addch(crash[0], crash[1], CRASH_CHAR)
            except curses.error:
                pass

        win.addstr(0, 2, f" Score: {score} ")

        if paused:
            msg = "PAUSED - press 'p' to resume"
            win.addstr(height // 2, max(1, (width - len(msg)) // 2), msg)

        win.refresh()
    except curses.error:
        log.exception(
            "curses draw error: snake=%s poop_count=%d food=%s score=%s height=%s width=%s",
            snake, len(poop), food, score, height, width,
        )
        raise


def show_game_over(win, score, height, width):
    """Overlay the game-over prompt without erasing the board, so the
    snake's final position and shape stay visible, and block for
    'r' (restart) or 'q' (quit)."""
    win.nodelay(False)
    lines = [
        "GAME OVER",
        f"Final score: {score}",
        "Press 'r' to restart or 'q' to quit",
    ]
    for i, line in enumerate(lines):
        win.addstr(height // 2 - 1 + i, max(1, (width - len(line)) // 2), line)
    win.refresh()

    while True:
        key = win.getch()
        if key in (ord("r"), ord("R")):
            return True
        if key in (ord("q"), ord("Q")):
            return False


def run_game(win, height, width):
    """Play one round. Returns the final score."""
    win.nodelay(True)
    win.timeout(DELAY_MS)
    win.keypad(True)

    mid_y, mid_x = height // 2, width // 2
    snake = [(mid_y, mid_x), (mid_y, mid_x - 1), (mid_y, mid_x - 2)]
    direction = (0, 1)
    poop = set()
    food = place_food(snake, poop, height, width)
    score = 0
    fruits_eaten = 0
    paused = False
    tick = 0

    log.info(
        "round start: board=%sx%s snake=%s direction=%s food=%s",
        height, width, snake, direction, food,
    )

    while True:
        tick += 1
        key = win.getch()
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
            draw_board(win, snake, poop, food, score, height, width, paused=True)
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
        collided_body = new_head in body_to_check
        collided_poop = new_head in poop
        if hit_wall or collided_body or collided_poop:
            log.warning(
                "tick=%d GAME OVER: head=%s new_head=%s hit_wall=%s collided_body=%s "
                "collided_poop=%s snake=%s poop_count=%d score=%d",
                tick, snake[0], new_head, hit_wall, collided_body, collided_poop,
                snake, len(poop), score,
            )
            draw_board(win, snake, poop, food, score, height, width, crash=new_head)
            return score, False

        snake.insert(0, new_head)

        if will_grow:
            score += 10
            fruits_eaten += 1
            if fruits_eaten % FRUITS_PER_POOP == 0:
                # The snake poops out its current tail cell as a permanent
                # obstacle once every FRUITS_PER_POOP fruits digested.
                poop.add(snake[-1])
                log.debug(
                    "tick=%d milestone: %d fruits eaten, poop added at %s",
                    tick, fruits_eaten, snake[-1],
                )
            food = place_food(snake, poop, height, width)
            log.debug("tick=%d ate food, new score=%d, new food=%s", tick, score, food)
        else:
            snake.pop()

        draw_board(win, snake, poop, food, score, height, width)


def main(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    log.info(
        "session start: board=%sx%s delay_ms=%d",
        height, width, DELAY_MS,
    )

    # Play on a window sized exactly to the logical board, not the full
    # terminal - stdscr.border() would otherwise draw around the whole
    # terminal while wall collisions are checked against height/width,
    # putting the visible border nowhere near where the game actually ends.
    win = curses.newwin(height, width, 0, 0)
    win.keypad(True)

    while True:
        score, quit_requested = run_game(win, height, width)
        if quit_requested:
            return
        if not show_game_over(win, score, height, width):
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
