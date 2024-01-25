#!/usr/bin/env python3

import random
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
        self.place_apple()

    def place_apple(self):
        # it's all a lie: the apple is never actually eaten, just moved around...
        # TODO: this will crash once there are no free cells left.
        # win the game in that case?
        self.apple = random.choice(self.free_cells)

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
                while not any((self.restart, self.exit)):
                    echo(t.clear)
                    self.draw(rectangle(self.width, self.height), (0,0), t.reverse)
                    self.draw(to_matrix(self.snake), (0,0), t.on_green)
                    self.draw(to_matrix([self.apple]), (0,0), t.on_red)
                    self.read_key()

    def read_key(self):
        t = self.term

        # TODO: make this timeout is the main clock, the longest interval between events
        val = t.inkey(timeout=1)

        if val.code == t.KEY_ESCAPE:
            self.exit = True
            return
        if val.code in [t.KEY_DELETE, t.KEY_BACKSPACE]:
            self.restart = True
            return

        def step(y, x):
            if (y, x) not in self.occupied_cells:
                self.snake = [(y, x)] + self.snake
                if (y, x) != self.apple:
                    self.snake = self.snake[:-1]
                else:
                    self.place_apple()

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

    @property
    def occupied_cells(self):
        return self.snake + to_coordinates(rectangle(self.width,self.height))

    @property
    def free_cells(self):
        padded = set()
        for y, x in self.occupied_cells:
            padded.update(get_neighbors(y, x, self.height, self.width))
        # XXX: this only works reliably because there is a rectangle at the
        # boundary in practice. to be more robust it needs explicit boundaries.
        # [tag:boundary]
        return complement_coordinates(list(padded))

    def draw(self, matrix, origin, color):
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
            row = (color("  ") if cell else t.move_right(2) for cell in matrix[y - origin_y])
            blit(''.join(row))
        sys.stdout.flush()

def rectangle(width, height):
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

def get_neighbors(y, x, max_y, max_x):
    return [(ny, nx) for nx in range(x-1, x+2) for ny in range(y-1, y+2)
            if 0 <= nx < max_x and 0 <= ny < max_y]

def complement_coordinates(coordinates):
    # TODO: this needs boundaries to be generally correct [ref:boundary]
    matrix = to_matrix(coordinates)
    return to_coordinates([[not cell for cell in row] for row in matrix])

if __name__ == "__main__":
    main()
