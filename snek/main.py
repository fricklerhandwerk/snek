#!/usr/bin/env python3

import signal
import sys
import time

from blessed import Terminal
from contextlib import contextmanager
from functools import partial

def main():
    Game(Terminal()).run()

# send characters to the terminal without updating
blit = partial(print, end='', flush=False)
# send characters to the terminal and update immediately
echo = partial(print, end='', flush=True)

class Game():
    def __init__(self, term):
        self.term = term
        self.reset()

    def reset(self):
        """
        Reset the game state
        """
        # terminal cells are narrow; use square pixels for simplicity [tag:pixels]
        self.width = self.term.width // 2
        self.height = self.term.height
        self.exit = False
        self.restart = False
        # the snake is a sequence of (y,x) coordinates,
        # the first element is the head
        self.snake = [(1,3),(1,2),(1,1)]

    @contextmanager
    def handle_resize(self):
        """
        Handle window resize events robustly [tag:resize]
        """

        def on_resize(signum, frame):
            # debounce bursts of resize events
            time.sleep(1/32)
            self.restart = True

        signal.signal(signal.SIGWINCH, on_resize)
        yield
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)

    def run(self):
        t = self.term

        with t.fullscreen(), t.raw(), t.hidden_cursor(), self.handle_resize():
            # TODO: show welcome screen with key bindings info and speed selection
            while not self.exit:
                self.reset()
                # TODO: set up game ticks with sched.scheduler
                while not any((self.restart, self.exit)):
                    echo(t.clear)
                    self.draw(self.rectangle(self.width, self.height), (0,0))
                    self.draw(to_matrix(self.snake), (0,0))
                    self.read_key()

    def read_key(self):
        t = self.term

        # timeout leaves opportunity for resize event handler to take effect [ref:resize]
        val = t.inkey(timeout=1)

        if val.code == t.KEY_ESCAPE:
            self.exit = True
            return
        if val.code in [t.KEY_DELETE, t.KEY_BACKSPACE]:
            self.restart = True
            return


        def step(y, x):
            if self.coordinate_valid(y, x):
                self.snake = [(y, x)] + self.snake[:-1]

        if val.code == t.KEY_DOWN:
            y, x = self.snake[0]
            step(y + 1, x)
        if val.code == t.KEY_UP:
            y, x = self.snake[0]
            step(y - 1, x)
        if val.code == t.KEY_LEFT:
            y, x = self.snake[0]
            step(y, x - 1)
        if val.code == t.KEY_RIGHT:
            y, x = self.snake[0]
            step(y, x + 1)

    def coordinate_valid(self, y, x):
        return (y, x) not in self.snake + to_coordinates(self.rectangle(self.width,self.height))

    def draw(self, matrix, origin):
        """
        Draw a binary `matrix` of square pixels [ref:pixels] on the screen starting at `origin`.
        """
        # TODO: add a double buffer and facilities for taking the difference,
        # draw only the change between the two
        origin_x, origin_y = origin

        t = self.term

        # compute visible area
        rows = set(range(origin_y, origin_y + len(matrix))) & set(range(self.height))
        columns = set(range(origin_x, origin_x + max(len(row) for row in matrix))) & set(range(self.width))

        for y in rows:
            blit(t.move(y, max(0, origin_x)))
            # [ref:pixels]
            row = (t.reverse("  ") if cell else t.move_right(2) for cell in matrix[y - origin_y])
            blit(''.join(row))
        sys.stdout.flush()

    def rectangle(self, width, height):
        matrix = []
        for y in range(height):
            row = []
            for x in range(width):
                if x in (0, width - 1) or y in (0, height - 1):
                    row.append(True)
                else:
                    row.append(False)
            matrix.append(row)
        return matrix

def to_matrix(coordinates):
    """
    Convert a sequence of coordinates to a binary matrix.
    """
    if not coordinates:
        return []

    max_y = max(coord[0] for coord in coordinates)
    max_x = max(coord[1] for coord in coordinates)

    matrix = [[False for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for y, x in coordinates:
        matrix[y][x] = True

    return matrix

def to_coordinates(matrix):
    """
    Convert a binary matrix to a sequence of coordinates
    """
    coordinates = []
    for x, row in enumerate(matrix):
        for y, value in enumerate(row):
            if value:
                coordinates.append((x, y))
    return coordinates

if __name__ == "__main__":
    main()
