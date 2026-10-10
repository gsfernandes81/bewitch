"""``Canvas``: a fixed-size surface to compose blocks onto, at a position.

Lip Gloss v2's ``Canvas`` in miniature: ``Canvas(width, height)``, then
:meth:`Canvas.compose` blocks at ``(x, y)``, later ones over earlier ones,
then :meth:`Canvas.render` to a :class:`Block` of exactly the canvas's size.
It is what a full screen is built on — the listing first, a dialog composed
over it, a spinner box over that — and nothing composed onto it can make it
grow: whatever falls off an edge is clipped.

A wide character is two columns. Composing over half of one turns the half
left behind into a space, so a canvas never holds a fragment of a character
the terminal would draw across its neighbour.
"""

from __future__ import annotations

from bewitch.lipgloss._cells import EMPTY, Block, Pen, Row, char_width

# A grid slot: (character, pen), or None for the second column of a wide
# character to its left.
_Slot = tuple[str, Pen] | None


class Canvas:
    __slots__ = ("_grid", "_width", "_height")

    def __init__(self, width: int, height: int):
        self._width = max(0, width)
        self._height = max(0, height)
        self._grid: list[list[_Slot]] = []
        self.clear()

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def clear(self) -> Canvas:
        self._grid = [[(" ", EMPTY)] * self._width for _ in range(self._height)]
        return self

    def resize(self, width: int, height: int) -> Canvas:
        """A new size, cleared — as Lip Gloss's ``Resize`` is."""
        self._width, self._height = max(0, width), max(0, height)
        return self.clear()

    def compose(self, block: Block, x: int = 0, y: int = 0) -> Canvas:
        """Draw *block* with its top-left corner at column *x*, row *y*."""
        for dy, row in enumerate(block.rows()):
            gy = y + dy
            if not 0 <= gy < self._height:
                continue
            gx = x
            for ch, pen in row:
                w = char_width(ch)
                if w == 0:
                    # A combining mark rides on whatever is to its left.
                    if 0 < gx <= self._width and self._grid[gy][gx - 1] is not None:
                        prev = self._grid[gy][gx - 1]
                        self._grid[gy][gx - 1] = (prev[0] + ch, prev[1])
                    continue
                if gx >= 0 and gx + w <= self._width:
                    self._put(gy, gx, ch, pen, w)
                elif gx < self._width and gx + w > 0:
                    # Straddles an edge: there is no half a character to draw.
                    for col in range(max(0, gx), min(self._width, gx + w)):
                        self._put(gy, col, " ", pen, 1)
                gx += w
        return self

    def _put(self, y: int, x: int, ch: str, pen: Pen, w: int) -> None:
        line = self._grid[y]
        last = x + w - 1
        # Landing on the right half of a wide character: blank its left half.
        if line[x] is None:
            line[x - 1] = (" ", line[x - 1][1])
        # Ending on the left half of one: blank its right half.
        tail = line[last]
        if tail is not None and char_width(tail[0][0]) == 2 and last + 1 < self._width:
            line[last + 1] = (" ", tail[1])
        line[x] = (ch, pen)
        for col in range(x + 1, last + 1):
            line[col] = None

    def render(self) -> Block:
        rows: list[Row] = [
            [slot for slot in line if slot is not None] for line in self._grid
        ]
        return Block.from_rows(rows, self._width)
