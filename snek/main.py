#!/usr/bin/env python3

import random

from typing import Any, List, Optional, Set, Tuple

from blessed import Terminal

from .screen import Buffer, Color, Coordinate, Screen, Shape


def main():
    Game(Terminal()).run()


class Game():
    def __init__(self, terminal):
        self.terminal = terminal
        self.screen = Screen(terminal)
        self.reset()

    def reset(self):
        """
        Reset the game state
        """
        self.screen.reset()
        self.width = self.screen.width
        self.height = self.screen.height
        self.exit = False
        self.restart = False
        # the snake is a sequence of (x,y) coordinates,
        # the first element is the head
        self.snake = [(3,1),(2,1),(1,1)]
        self.obstacles = rectangle(self.width, self.height)
        self.place_apple()

    def place_apple(self):
        # it's all a lie: the apple is never actually eaten, just moved around...
        # TODO: this will crash once there are no free cells left.
        # win the game in that case?
        self.apple = random.choice(list(self.free_cells))

    def run(self):
        t = self.terminal

        def on_resize():
            self.restart = True

        with t.fullscreen(), t.raw(), t.hidden_cursor(), self.screen.handle_resize(on_resize):
            print(t.clear)
            # TODO: show welcome screen with key bindings info and speed selection
            while not self.exit:
                self.reset()
                while not any((self.restart, self.exit)):
                    background = self.screen.buffer()
                    background.contents = [[Color.black for x in y] for y in background.contents]
                    obstacles = Shape(Color.white, self.obstacles)
                    snake = Shape(Color.green, set(self.snake))
                    apple = Shape(Color.red, set([self.apple]))
                    self.screen.overlay(background)
                    self.screen.draw(obstacles)
                    self.screen.draw(snake)
                    self.screen.draw(apple)
                    self.screen.update()
                    self.read_key()

    def read_key(self):
        # TODO: factor out input processing, and make inputs map to game methods
        t = self.terminal

        # TODO: make this timeout is the main clock, the longest interval between events
        val = t.inkey(timeout=1)

        if val.code == t.KEY_ESCAPE:
            self.exit = True
            return
        if val.code in [t.KEY_DELETE, t.KEY_BACKSPACE]:
            self.restart = True
            return

        def step(x, y):
            if (x, y) not in self.occupied_cells:
                self.snake = [(x, y)] + self.snake
                if (x, y) != self.apple:
                    self.snake = self.snake[:-1]
                else:
                    self.place_apple()

        if val.code == t.KEY_DOWN:
            x, y = self.snake[0]
            step(x, y + 1)
        if val.code == t.KEY_UP:
            x, y = self.snake[0]
            step(x, y - 1)
        if val.code == t.KEY_LEFT:
            x, y = self.snake[0]
            step(x - 1, y)
        if val.code == t.KEY_RIGHT:
            x, y = self.snake[0]
            step(x + 1, y)

    @property
    def occupied_cells(self):
        return set(self.snake) | self.obstacles

    @property
    def free_cells(self) -> Set[Coordinate]:
        padded = Shape(color=Color.white)

        def get_neighbors(c: Coordinate) -> Set[Coordinate]:
            x, y = c
            return set((nx, ny) for nx in range(x-1, x+2) for ny in range(y-1, y+2))

        for cell in self.occupied_cells:
            padded.coordinates.update(get_neighbors(cell))

        buffer = self.screen.buffer()
        buffer.draw(padded)

        free = set()
        for y, row in enumerate(buffer.contents):
            for x, value in enumerate(row):
                if not value:
                    free.add((x, y))

        return free


def rectangle(width: int, height: int) -> Set[Coordinate]:
    coordinates = set()
    for y in range(height):
        for x in range(width):
            if x in (0, width - 1) or y in (0, height - 1):
                coordinates.add((x, y))
    return coordinates


if __name__ == "__main__":
    main()
