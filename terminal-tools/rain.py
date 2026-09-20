#!/usr/bin/env python3
"""A tiny animated rain effect for an ANSI terminal. Stop with Ctrl+C."""
import curses
import random
import time

CHARS = "|.'`/"


def animate(screen):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.timeout(40)
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_BLUE, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
    except curses.error:
        pass
    height, width = screen.getmaxyx()
    drops = [[random.randrange(max(width, 1)), random.randrange(max(height, 1))]
             for _ in range(max(12, width // 2))]
    colors = [curses.color_pair(i) if curses.has_colors() else 0 for i in (1, 2, 3)]
    while True:
        height, width = screen.getmaxyx()
        if height < 3 or width < 8:
            time.sleep(.2)
            continue
        screen.erase()
        for x, y in drops:
            if x < width and y < height - 1:
                try:
                    screen.addstr(y, x, random.choice(CHARS), random.choice(colors))
                except curses.error:
                    pass
        try:
            screen.addstr(height - 1, 0, "  terminal rain  ·  press q or Ctrl+C to quit "[:width - 1], curses.A_DIM)
        except curses.error:
            pass
        screen.refresh()
        key = screen.getch()
        if key in (ord('q'), ord('Q'), 27):
            break
        for drop in drops:
            if random.random() < .14:
                drop[1] = 0
                drop[0] = random.randrange(width)
            else:
                drop[1] += random.choice((1, 1, 1, 2))
            if drop[1] >= height - 1:
                drop[1] = 0
                drop[0] = random.randrange(width)


def main():
    try:
        curses.wrapper(animate)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
