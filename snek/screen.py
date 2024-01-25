"""
Utilties for rendering square pixels to a terminal screen.
"""

import signal
import sys

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

import blessed
from blessed.colorspace import RGBColor


Coordinate = Tuple[int, int]


class ColorNames(type):
    def __getattr__(cls, color_name):
        try:
            return blessed.colorspace.X11_COLORNAMES_TO_RGB[color_name]
        except KeyError:
            raise AttributeError(f"Color '{color_name}' not found") from None


class Color(metaclass=ColorNames):
    """
    Utility wrapper for named colors.

    Example:
    >>> Color.red
    RGBColor(red=255, green=0, blue=0)
    """
    pass


@dataclass
class Shape:
    """
    Single-colored pixel pattern.
    """
    color: RGBColor
    coordinates: Set[Coordinate] = field(default_factory=set)


class Buffer:
    """
    Buffer for colored or transparent pixels.
    """
    contents: List[List[Optional[RGBColor]]]
    width: int
    height: int

    def __init__(self, width: int, height: int):
        self.contents = [[None for x in range(width)] for y in range(height)]
        self.width = width
        self.height = height

    def __sub__(self, other: "Buffer") -> "Buffer":
        """
        Take the difference to a buffer of the same size.
        For values that differ, the one from this object appears in the result.
        """
        if self.width != other.width or self.height != other.height:
            raise ValueError("Buffers must have the same dimensions")

        return [[col1 if col1 != col2 else None for col1, col2 in zip(row1, row2)]
                for row1, row2 in zip(self.contents, other.contents)]


class Screen:
    """
    Model of a terminal screen with quadratic pixels.
    """

    terminal: blessed.Terminal
    # double buffer for efficent updates
    current: Buffer
    previous: Buffer
    # whether the terminal was resized
    resized: bool = False

    def __init__(self, terminal: blessed.Terminal):
        self.terminal = terminal
        self.reset()

    def reset(self):
        """
        Reset the screen buffer to the terminal size.
        """
        self.current = self.buffer()
        self.previous = self.buffer()
        self.resized = False

    def buffer(self):
        """
        Create an empty buffer that matches the terminal size in square pixels.
        """
        return Buffer(width=self.terminal.width // 2, height=self.terminal.height)

    @property
    def width(self):
        return self.current.width

    @property
    def height(self):
        return self.current.height

    @contextmanager
    def handle_resize(self, handler=None):
        """
        Catch window resize signals and set `resized = True`.
        Set `handler` to be run on a resize signal.

        Resize signals come in high-frequency bursts when a window is resized by dragging the mouse!
        Therefore, the `handler` should be either very cheap or (re-)schedule expensive work with a delay (debounce)
        """

        def on_resize(signum, frame):
            self.resized = True
            if handler:
                handler()

        signal.signal(signal.SIGWINCH, on_resize)
        yield
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)

    def update(self):
        """
        Update the terminal with the contents of the screen buffer.
        """
        # write a sequence of colored squares to the terminal
        write = lambda seq: blit("".join([colored(px) for px in seq]))

        # square pixels: convert a pixel to a colored double space
        colored = lambda px: self.terminal.on_color_rgb(*px)("  ")

        # send characters to the terminal without updating
        blit = lambda s: print(s, end='', flush=False)

        for y, row in enumerate(self.current - self.previous):
            sequence = []
            for x, pixel in enumerate(row):
                if pixel is not None:
                    if not sequence:
                        # square pixels: move twice the horizontal width
                        blit(self.terminal.move(y, x * 2))
                    sequence.append(pixel)
                elif sequence:
                    write(sequence)
                    sequence = []
            write(sequence)
        sys.stdout.flush()

        # swap buffers
        self.previous = self.current
        self.current = self.buffer()


    def draw(self, shape: Shape):
        """
        Draw a shape onto the screen buffer.
        """
        draw(self.current, shape)


def draw(buffer: Buffer, shape: Shape):
    """
    Draw a Shape onto a Buffer.
    """
    for x, y in shape.coordinates:
        if 0 <= x < buffer.width and 0 <= y < buffer.height:
            buffer.contents[x][y] = shape.color
