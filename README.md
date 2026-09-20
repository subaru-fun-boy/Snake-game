# Snake

A classic Snake game for the terminal, written in Python using `curses`.

This repo also serves as a small demo of working with Claude Code: writing
code, running checks, and building up a git history.

## Requirements

- Python 3 (uses only the standard library, including `curses`)
- A real terminal (curses needs a TTY, so it won't run inside non-interactive
  shells or most IDE output panes)

## Run

```bash
python3 snake.py
```

## Controls

| Key          | Action          |
|--------------|-----------------|
| Arrow keys   | Move the snake  |
| `p`          | Pause / resume  |
| `q`          | Quit            |
| `r`          | Restart (after game over) |

## Rules

- The board fills the whole terminal window.
- Eat food (`◆`) to grow and score points.
- Every cell your tail leaves behind turns into permanent "poop" (`%`) -
  it never disappears, so you can't cross your own trail again.
- Hitting a wall, your own body, or a poop cell ends the game. The board
  freezes at the moment of the crash (with an `X` marking the impact) so
  you can see exactly what went wrong.
