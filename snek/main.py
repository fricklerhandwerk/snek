#!/usr/bin/env python3

import random

from enum import Enum
from typing import Any, List, Optional, Set, Tuple

from blessed import Terminal

from .screen import Buffer, Color, Coordinate, Screen, Shape


def main():
    Game(Terminal()).run()

class Direction(Enum):
    Up = (0, -1)
    Down = (0, 1)
    Left = (-1, 0)
    Right = (1, 0)

class Snake:
    body: List[Coordinate]
    direction: Direction

    def __init__(self, head: Coordinate, length: int, direction: Direction):
        x, y = head
        dx, dy = direction.value
        self.body = [(x - dx * i, y - dy * i) for i in range(length)]

    def shape(self, color: Color):
        return Shape(color=color,coordinates=set(self.body))

    @property
    def head(self):
        return self.body[0]

    def move(self, direction: Direction, grow: bool = False):
        hx, hy = self.head
        dx, dy = direction.value
        self.body = [(hx + dx, hy + dy)] + self.body
        if not grow:
            self.body = self.body[:-1]

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
        self.snake_1 = Snake(head=(3,1), length=3, direction=Direction.Right)
        self.snake_2 = Snake(head=(self.width-4,self.height-2), length=3, direction=Direction.Left)
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

                background = self.screen.buffer()
                background.contents = [[Color.black for x in y] for y in background.contents]

                while not any((self.restart, self.exit)):
                    obstacles = Shape(Color.white, self.obstacles)
                    apple = Shape(Color.red, set([self.apple]))
                    self.screen.overlay(background)
                    self.screen.draw(obstacles)
                    self.screen.draw(self.snake_1.shape(Color.green))
                    self.screen.draw(self.snake_2.shape(Color.pink))
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

        # left player
        if val == 's':
            self.move(self.snake_1, Direction.Down)
        if val == 'w':
            self.move(self.snake_1, Direction.Up)
        if val == 'a':
            self.move(self.snake_1, Direction.Left)
        if val == 'd':
            self.move(self.snake_1, Direction.Right)

        # right player
        if val.code == t.KEY_DOWN:
            self.move(self.snake_2, Direction.Down)
        if val.code == t.KEY_UP:
            self.move(self.snake_2, Direction.Up)
        if val.code == t.KEY_LEFT:
            self.move(self.snake_2, Direction.Left)
        if val.code == t.KEY_RIGHT:
            self.move(self.snake_2, Direction.Right)

    def move(self, snake, direction):
        """
        Move a snake in the given direction.
        """
        hx, hy = snake.head
        dx, dy = direction.value
        new_position = (hx + dx, hy + dy)
        if new_position not in self.occupied_cells:
            found_apple = new_position == self.apple
            if found_apple:
                self.place_apple()
            snake.move(direction, found_apple)

    @property
    def occupied_cells(self):
        return set(self.snake_1.body) | set(self.snake_2.body) | self.obstacles

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
