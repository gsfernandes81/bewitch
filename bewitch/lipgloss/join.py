"""Putting blocks side by side, on top of each other, and in a space.

Positions are Lip Gloss's: a float from 0 to 1, where ``TOP``/``LEFT`` are 0,
``CENTER`` is 0.5 and ``BOTTOM``/``RIGHT`` are 1, and anything between is a
proportion. Rounding is Go's (half away from zero), not Python's banker's
rounding, so a block lands in the cell Lip Gloss would put it in.
"""

from __future__ import annotations

import math

from bewitch.lipgloss._cells import EMPTY, Block, Pen, Row, blank, row_width

Position = float

TOP: Position = 0.0
LEFT: Position = 0.0
CENTER: Position = 0.5
BOTTOM: Position = 1.0
RIGHT: Position = 1.0


def _round(x: float) -> int:
    return int(math.floor(x + 0.5))


def _clamp(pos: Position) -> float:
    return min(1.0, max(0.0, pos))


def join_horizontal(pos: Position, *blocks: Block) -> Block:
    """Blocks side by side, the shorter ones padded to the tallest.

    *pos* says where a shorter block sits: ``TOP``, ``CENTER``, ``BOTTOM`` or
    a proportion. The result is exactly as wide as the blocks added up.
    """
    if not blocks:
        return Block()
    tallest = max(b.height for b in blocks)
    columns = [_pad_vertical(b, tallest, pos) for b in blocks]
    rows: list[Row] = [[] for _ in range(tallest)]
    for column in columns:
        for i, row in enumerate(column):
            rows[i].extend(row)
    return Block.from_rows(rows, sum(b.width for b in blocks))


def join_vertical(pos: Position, *blocks: Block) -> Block:
    """Blocks stacked, the narrower ones padded to the widest.

    *pos* says where a narrower block sits: ``LEFT``, ``CENTER``, ``RIGHT``
    or a proportion. The result is exactly as tall as the blocks added up.
    """
    if not blocks:
        return Block()
    widest = max(b.width for b in blocks)
    rows: list[Row] = []
    for block in blocks:
        for row in block.rows():
            rows.append(_pad_horizontal(row, widest, pos))
    return Block.from_rows(rows, widest)


def place(
    width: int,
    height: int,
    hpos: Position,
    vpos: Position,
    block: Block,
    whitespace: Pen = EMPTY,
) -> Block:
    """*block* placed in a *width* by *height* space.

    The space never shrinks below the block: a block bigger than it is
    returned whole, as Lip Gloss's ``Place`` does. *whitespace* is the pen
    the empty space is drawn with.
    """
    return place_vertical(
        height, vpos, place_horizontal(width, hpos, block, whitespace), whitespace
    )


def place_horizontal(
    width: int, pos: Position, block: Block, whitespace: Pen = EMPTY
) -> Block:
    target = max(width, block.width)
    return Block.from_rows(
        (_pad_horizontal(r, target, pos, whitespace) for r in block.rows()), target
    )


def place_vertical(
    height: int, pos: Position, block: Block, whitespace: Pen = EMPTY
) -> Block:
    rows = _pad_vertical(block, max(height, block.height), pos, whitespace)
    return Block.from_rows(rows, block.width)


def _pad_horizontal(row: Row, target: int, pos: Position, pen: Pen = EMPTY) -> Row:
    gap = target - row_width(row)
    if gap <= 0:
        return list(row)
    left = _round(gap * _clamp(pos))
    return blank(left, pen) + list(row) + blank(gap - left, pen)


def _pad_vertical(
    block: Block, target: int, pos: Position, pen: Pen = EMPTY
) -> list[Row]:
    rows = block.rows()
    gap = target - len(rows)
    if gap <= 0:
        return rows
    top = _round(gap * _clamp(pos))
    filler = blank(block.width, pen)
    return (
        [list(filler) for _ in range(top)]
        + rows
        + [list(filler) for _ in range(gap - top)]
    )
