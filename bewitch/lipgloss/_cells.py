"""Cells, pens, spans and blocks: what every render is made of.

Lip Gloss renders to a string with the escape sequences already in it, and
measures that string by stripping them again. Here a render is a
:class:`Block` — a rectangle of :class:`Span` runs, each carrying its own
:class:`Pen` — and escape sequences are only written at the very end, by an
adapter, for the terminal or library that is actually drawing. That is what
lets the same render go to ``print()``, to blessed, to curses (which corrupts
on raw escapes) or to Rich.

It also makes nesting honest. A Lip Gloss string rendered inside another
style ends in a reset, so the outer style is lost after the first inner
piece. A pen here leaves an attribute unset (``None``) rather than off, and
an unset attribute takes the outer style's value — so an inner span with no
background sits on the outer background, which is what a person meant.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, fields
from functools import lru_cache

from bewitch.color import Color


@dataclass(frozen=True, slots=True)
class Pen:
    """How a run of text is drawn. ``None`` means "inherit", never "off"."""

    fg: Color | None = None
    bg: Color | None = None
    bold: bool | None = None
    faint: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikethrough: bool | None = None
    reverse: bool | None = None

    def over(self, base: Pen) -> Pen:
        """This pen, with anything it leaves unset taken from *base*."""
        if base is EMPTY:
            return self
        if self is EMPTY:
            return base
        return Pen(
            *(
                mine if mine is not None else theirs
                for mine, theirs in zip(_values(self), _values(base), strict=True)
            )
        )

    @property
    def is_plain(self) -> bool:
        """True when drawing with this pen needs no escape sequence at all."""
        return all(v is None or v is False for v in _values(self))


def _values(pen: Pen) -> tuple:
    return tuple(getattr(pen, f.name) for f in fields(pen))


EMPTY = Pen()


@dataclass(frozen=True, slots=True)
class Span:
    """A run of text drawn with one pen. It never holds a newline."""

    text: str
    pen: Pen = EMPTY

    @property
    def width(self) -> int:
        return string_width(self.text)


# A cell is one character and its pen. Wide characters are one cell of
# width 2; zero-width marks ride on the character before them.
Cell = tuple[str, Pen]
Row = list[Cell]


@lru_cache(maxsize=4096)
def char_width(ch: str) -> int:
    """Columns *ch* takes in a terminal.

    East Asian Wide and Fullwidth are two. Combining marks, format
    characters (ZWJ, the variation selectors) and controls are zero.
    Everything else is one — East Asian *Ambiguous* included (``│``, ``…``,
    ``•``), because that is how Termux and every Western terminal draw them,
    and it was checked on the phone this package was written for.
    """
    if unicodedata.combining(ch):
        return 0
    category = unicodedata.category(ch)
    if category in ("Mn", "Me", "Cf", "Cc"):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def string_width(text: str) -> int:
    """Columns a single line of *text* takes."""
    if text.isascii() and text.isprintable():
        return len(text)
    return sum(char_width(ch) for ch in text)


def width(text: str) -> int:
    """The widest line of *text*, in columns — Lip Gloss's ``Width``."""
    return max((string_width(line) for line in text.split("\n")), default=0)


def height(text: str) -> int:
    """How many lines *text* is — Lip Gloss's ``Height``."""
    return text.count("\n") + 1


def row_width(row: Row) -> int:
    return sum(char_width(ch) for ch, _ in row)


def to_row(text: str, pen: Pen = EMPTY) -> Row:
    return [(ch, pen) for ch in text]


def blank(n: int, pen: Pen = EMPTY) -> Row:
    return [(" ", pen)] * max(0, n)


def truncate_row(row: Row, limit: int, tail: Row | None = None) -> Row:
    """*row* cut to *limit* columns, ending in *tail* if anything was cut.

    A wide character that would straddle the limit is dropped rather than
    split; the row comes back narrower by one, and padding is the caller's
    business, because only the caller knows which pen the gap should have.
    """
    if row_width(row) <= limit:
        return list(row)
    tail = tail or []
    room = limit - row_width(tail)
    if room < 0:
        return truncate_row(tail, limit)
    out: Row = []
    used = 0
    for cell in row:
        w = char_width(cell[0])
        if used + w > room:
            break
        # A zero-width mark never trips the limit, so it stays with the
        # character before it.
        out.append(cell)
        used += w
    return out + tail


def truncate(text: str, limit: int, tail: str = "") -> str:
    """A single line cut to *limit* columns, ending in *tail* if cut."""
    return "".join(ch for ch, _ in truncate_row(to_row(text), limit, to_row(tail)))


def wrap_row(row: Row, limit: int) -> list[Row]:
    """Word-wrap one row to *limit* columns.

    Spaces between words are kept, spaces at a break are dropped, leading
    spaces (indentation) are kept on the first line, and a word longer than
    the whole line is broken hard. A hyphen is not a break point — the same
    rule ytq sets on ``textwrap``, because a path broken across two lines is
    a path retyped wrong.
    """
    if limit <= 0:
        return [list(row)]
    if row_width(row) <= limit:
        return [list(row)]
    lines: list[Row] = []
    line: Row = []
    used = 0
    pending: Row = []
    for token in _tokens(row):
        if token[0][0] == " ":
            pending = token
            continue
        w = row_width(token)
        gap = row_width(pending)
        if line and used + gap + w <= limit:
            line += pending + token
            used += gap + w
        elif not line and not lines and gap + w <= limit:
            line = pending + token
            used = gap + w
        else:
            if line:
                lines.append(line)
            line, used = [], 0
            while w > limit:
                head = truncate_row(token, limit)
                if not head:  # a wide char that cannot fit at all
                    head, token = token[:1], token[1:]
                else:
                    token = token[len(head) :]
                lines.append(head)
                w = row_width(token)
            line, used = list(token), w
        pending = []
    if line or not lines:
        lines.append(line)
    return lines


def _tokens(row: Row) -> Iterator[Row]:
    """Alternating runs of spaces and of everything else."""
    current: Row = []
    for cell in row:
        if current and (cell[0] == " ") != (current[0][0] == " "):
            yield current
            current = []
        current.append(cell)
    if current:
        yield current


def spans_of(row: Row) -> tuple[Span, ...]:
    """A row of cells folded back into as few spans as it takes."""
    spans: list[Span] = []
    text: list[str] = []
    pen: Pen | None = None
    for ch, cell_pen in row:
        if cell_pen is not pen and cell_pen != pen and text:
            spans.append(Span("".join(text), pen or EMPTY))
            text = []
        pen = cell_pen
        text.append(ch)
    if text:
        spans.append(Span("".join(text), pen or EMPTY))
    return tuple(spans)


def cells_of(spans: Iterable[Span]) -> Row:
    return [(ch, span.pen) for span in spans for ch in span.text]


class Block:
    """A rendered rectangle: every line exactly :attr:`width` columns.

    This is what :meth:`Style.render` returns where Lip Gloss returns a
    string. ``str(block)`` writes it for the terminal on stdout, at whatever
    colour that terminal supports; :mod:`bewitch.ansi` does the same for an
    explicit profile, and :meth:`plain` gives the text with no styling.
    """

    __slots__ = ("lines", "width")

    def __init__(self, lines: Iterable[Iterable[Span]] = (), width: int | None = None):
        rows = [cells_of(line) for line in lines]
        widest = max((row_width(r) for r in rows), default=0)
        self.width = widest if width is None else width
        self.lines: tuple[tuple[Span, ...], ...] = tuple(
            spans_of(_fit(r, self.width)) for r in rows
        )

    @classmethod
    def from_rows(cls, rows: Iterable[Row], width: int | None = None) -> Block:
        block = cls.__new__(cls)
        rows = list(rows)
        widest = max((row_width(r) for r in rows), default=0)
        block.width = widest if width is None else width
        block.lines = tuple(spans_of(_fit(r, block.width)) for r in rows)
        return block

    @classmethod
    def text(cls, text: str, pen: Pen = EMPTY) -> Block:
        """A block of plain *text*, one line per ``\\n``, left-aligned."""
        return cls.from_rows(to_row(line, pen) for line in text.split("\n"))

    @property
    def height(self) -> int:
        return len(self.lines)

    def rows(self) -> list[Row]:
        return [cells_of(line) for line in self.lines]

    def plain(self) -> str:
        """The text of the block, no styling, lines joined with ``\\n``."""
        return "\n".join("".join(s.text for s in line) for line in self.lines)

    def __str__(self) -> str:
        from bewitch import ansi

        return ansi.render(self)

    def __repr__(self) -> str:
        return f"<Block {self.width}x{self.height} {self.plain()[:40]!r}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Block):
            return NotImplemented
        return self.width == other.width and self.lines == other.lines

    def __hash__(self) -> int:
        return hash((self.width, self.lines))


def _fit(row: Row, target: int) -> Row:
    """*row* made exactly *target* columns: cut if long, padded if short."""
    w = row_width(row)
    if w > target:
        row = truncate_row(row, target)
        w = row_width(row)
    if w < target:
        # Unstyled on purpose: an unset pen inherits from whatever style this
        # block is rendered inside, so the gap takes that style's background.
        row = row + blank(target - w)
    return row
