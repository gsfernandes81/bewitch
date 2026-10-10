"""``Style``: Lip Gloss's style, ported to Python.

The methods are Lip Gloss v2's (v2.0.6) in Python spelling — ``Foreground``
is :meth:`Style.foreground`, ``BorderForeground`` is
:meth:`Style.border_foreground` — and a style is immutable the same way: every
setter returns a new style. The render follows Lip Gloss's own order, step for
step: wrap, colour the text, pad, set the height, align, border, margin,
then cut to the maximum size.

Three differences, all on purpose:

* :meth:`Style.render` returns a :class:`~bewitch.lipgloss.Block`, not a
  string with the escape sequences in it (see :mod:`bewitch.lipgloss._cells`
  for why). ``str()`` of it is the string Lip Gloss would have given.
* **Width is exact.** As in Lip Gloss v2, ``width`` counts the border and the
  padding and not the margin. Text is wrapped to fit it, as Lip Gloss does;
  a *Block* rendered into a narrower style is cut to fit, where Lip Gloss
  would wrap its escape-laden lines. A layout that says 38 columns gets 38.
* Text arrives as ``str``, a :class:`Span` or a list of spans, never as a
  string with escape sequences inside it. Styled pieces are spans.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from bewitch.color import Color, ColorLike, to_color
from bewitch.lipgloss._cells import (
    EMPTY,
    Block,
    Pen,
    Row,
    Span,
    blank,
    cells_of,
    row_width,
    to_row,
    truncate_row,
    wrap_row,
)
from bewitch.lipgloss.borders import Border
from bewitch.lipgloss.join import LEFT, TOP, Position, _pad_horizontal

Content = str | Span | Sequence[Span] | Block


def _sides(values: Sequence, what: str) -> tuple:
    """CSS shorthand: 1 value is all sides, 2 is vertical/horizontal,
    3 is top/horizontal/bottom, 4 is top/right/bottom/left."""
    if len(values) == 1:
        return (values[0],) * 4
    if len(values) == 2:
        return (values[0], values[1], values[0], values[1])
    if len(values) == 3:
        return (values[0], values[1], values[2], values[1])
    if len(values) == 4:
        return tuple(values)
    raise TypeError(f"{what} takes 1 to 4 values, got {len(values)}")


@dataclass(frozen=True, slots=True)
class _Props:
    pen: Pen = EMPTY
    width: int = 0
    height: int = 0
    max_width: int = 0
    max_height: int = 0
    align_h: Position = LEFT
    align_v: Position = TOP
    padding: tuple[int, int, int, int] = (0, 0, 0, 0)
    margin: tuple[int, int, int, int] = (0, 0, 0, 0)
    margin_bg: Color | None = None
    border: Border | None = None
    # None: "every side, because a border was set without naming any".
    border_sides: tuple[bool, bool, bool, bool] | None = None
    border_fg: tuple[Color | None, ...] = (None, None, None, None)
    border_bg: tuple[Color | None, ...] = (None, None, None, None)
    inline: bool = False
    color_whitespace: bool = True
    tab_width: int = 4
    transform: Callable[[str], str] | None = field(default=None, compare=False)


class Style:
    """A Lip Gloss style. Build one with chained calls, then :meth:`render`.

    >>> from bewitch import charmtone
    >>> title = Style().foreground(charmtone.Charple).bold().padding(0, 1)
    >>> title.render("Results").plain()
    ' Results '
    """

    __slots__ = ("_p",)

    def __init__(self, _props: _Props | None = None):
        self._p = _props or _Props()

    def _with(self, **changes) -> Style:
        return Style(replace(self._p, **changes))

    def _pen(self, **changes) -> Style:
        return self._with(pen=replace(self._p.pen, **changes))

    def __repr__(self) -> str:
        return f"Style({self._p})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Style) and self._p == other._p

    def __hash__(self) -> int:
        return hash(self._p)

    # Text attributes -------------------------------------------------------

    def foreground(self, color: ColorLike | None) -> Style:
        return self._pen(fg=to_color(color))

    def background(self, color: ColorLike | None) -> Style:
        return self._pen(bg=to_color(color))

    def bold(self, on: bool = True) -> Style:
        return self._pen(bold=on)

    def faint(self, on: bool = True) -> Style:
        return self._pen(faint=on)

    def italic(self, on: bool = True) -> Style:
        return self._pen(italic=on)

    def underline(self, on: bool = True) -> Style:
        return self._pen(underline=on)

    def strikethrough(self, on: bool = True) -> Style:
        return self._pen(strikethrough=on)

    def reverse(self, on: bool = True) -> Style:
        return self._pen(reverse=on)

    # Size and alignment ----------------------------------------------------

    def width(self, n: int) -> Style:
        """The whole width, border and padding included, margin not."""
        return self._with(width=max(0, n))

    def height(self, n: int) -> Style:
        """The least height, border and padding included, margin not."""
        return self._with(height=max(0, n))

    def max_width(self, n: int) -> Style:
        """Cut every line to *n* columns, after everything else."""
        return self._with(max_width=max(0, n))

    def max_height(self, n: int) -> Style:
        """Keep the first *n* lines, after everything else."""
        return self._with(max_height=max(0, n))

    def align(self, horizontal: Position, vertical: Position | None = None) -> Style:
        s = self._with(align_h=horizontal)
        return s if vertical is None else s._with(align_v=vertical)

    def align_horizontal(self, pos: Position) -> Style:
        return self._with(align_h=pos)

    def align_vertical(self, pos: Position) -> Style:
        return self._with(align_v=pos)

    def inline(self, on: bool = True) -> Style:
        """One line: newlines dropped, and no padding, border or margin."""
        return self._with(inline=on)

    def color_whitespace(self, on: bool = True) -> Style:
        """Whether padding and alignment space take the background."""
        return self._with(color_whitespace=on)

    def tab_width(self, n: int) -> Style:
        """Spaces per tab; ``-1`` leaves tabs alone. Lip Gloss's default is 4."""
        return self._with(tab_width=n)

    def transform(self, fn: Callable[[str], str] | None) -> Style:
        """A function applied to plain-text content before anything else."""
        return self._with(transform=fn)

    # Padding and margin ----------------------------------------------------

    def padding(self, *values: int) -> Style:
        return self._with(padding=tuple(max(0, v) for v in _sides(values, "padding")))

    def padding_top(self, n: int) -> Style:
        return self._side("padding", 0, n)

    def padding_right(self, n: int) -> Style:
        return self._side("padding", 1, n)

    def padding_bottom(self, n: int) -> Style:
        return self._side("padding", 2, n)

    def padding_left(self, n: int) -> Style:
        return self._side("padding", 3, n)

    def margin(self, *values: int) -> Style:
        return self._with(margin=tuple(max(0, v) for v in _sides(values, "margin")))

    def margin_top(self, n: int) -> Style:
        return self._side("margin", 0, n)

    def margin_right(self, n: int) -> Style:
        return self._side("margin", 1, n)

    def margin_bottom(self, n: int) -> Style:
        return self._side("margin", 2, n)

    def margin_left(self, n: int) -> Style:
        return self._side("margin", 3, n)

    def margin_background(self, color: ColorLike | None) -> Style:
        return self._with(margin_bg=to_color(color))

    def _side(self, which: str, index: int, n: int) -> Style:
        values = list(getattr(self._p, which))
        values[index] = max(0, n)
        return self._with(**{which: tuple(values)})

    # Borders ---------------------------------------------------------------

    def border(self, border: Border, *sides: bool) -> Style:
        """A border, on the sides given in CSS order, or on all of them."""
        s = self._with(border=border)
        return s._with(border_sides=_sides(sides, "border sides")) if sides else s

    def border_style(self, border: Border) -> Style:
        return self._with(border=border)

    def border_top(self, on: bool = True) -> Style:
        return self._border_side(0, on)

    def border_right(self, on: bool = True) -> Style:
        return self._border_side(1, on)

    def border_bottom(self, on: bool = True) -> Style:
        return self._border_side(2, on)

    def border_left(self, on: bool = True) -> Style:
        return self._border_side(3, on)

    def _border_side(self, index: int, on: bool) -> Style:
        # Naming one side turns the others off unless they are named too —
        # Lip Gloss's rule: "all sides" holds only while no side is set.
        sides = list(self._p.border_sides or (False, False, False, False))
        sides[index] = on
        return self._with(border_sides=tuple(sides))

    def border_foreground(self, *colors: ColorLike | None) -> Style:
        return self._with(
            border_fg=tuple(to_color(c) for c in _sides(colors, "border_foreground"))
        )

    def border_background(self, *colors: ColorLike | None) -> Style:
        return self._with(
            border_bg=tuple(to_color(c) for c in _sides(colors, "border_background"))
        )

    # Composition -----------------------------------------------------------

    def inherit(self, other: Style) -> Style:
        """This style, with what it leaves unset taken from *other*.

        As in Lip Gloss, padding and margins are not inherited, and only
        text attributes and the background are — a style is a recipe, and a
        size belongs to the recipe that set it.
        """
        return self._with(pen=self._p.pen.over(other._p.pen))

    def get_horizontal_frame_size(self) -> int:
        """Columns the border, padding and margin take, left and right."""
        p = self._p
        return (
            p.padding[1]
            + p.padding[3]
            + p.margin[1]
            + p.margin[3]
            + sum(self._border_widths()[1::2])
        )

    def get_vertical_frame_size(self) -> int:
        """Rows the border, padding and margin take, top and bottom."""
        p = self._p
        return (
            p.padding[0]
            + p.padding[2]
            + p.margin[0]
            + p.margin[2]
            + sum(self._border_widths()[0::2])
        )

    def _active_sides(self) -> tuple[bool, bool, bool, bool]:
        p = self._p
        if p.border is None or p.border == Border():
            return (False, False, False, False)
        return p.border_sides or (True, True, True, True)

    def _border_widths(self) -> tuple[int, int, int, int]:
        top, right, bottom, left = self._active_sides()
        b = self._p.border
        return (
            1 if top else 0,
            (row_width(to_row(b.right)) or 1) if right else 0,
            1 if bottom else 0,
            (row_width(to_row(b.left)) or 1) if left else 0,
        )

    # Rendering -------------------------------------------------------------

    def render(self, *parts: Content) -> Block:
        """Lay out *parts* in this style.

        Several parts are joined with a space, as Lip Gloss's ``Render``
        joins its strings. A :class:`Block` must come alone: it is already
        laid out, and there is no single right way to set text beside it —
        that is what :func:`join_horizontal` is for.
        """
        p = self._p
        rows, laid_out = self._content(parts)
        pen = p.pen

        if p.inline:
            rows = [[cell for row in rows for cell in row]]

        top_b, right_b, bottom_b, left_b = self._border_widths()
        width = p.width - left_b - right_b if p.width else 0
        height = p.height - top_b - bottom_b if p.height else 0
        pad_t, pad_r, pad_b, pad_l = (0, 0, 0, 0) if p.inline else p.padding

        text_width = width - pad_l - pad_r if width else 0
        if text_width > 0 or (width and laid_out):
            text_width = max(0, text_width)
            if laid_out:
                rows = [truncate_row(r, text_width) for r in rows]
            elif not p.inline:
                # The cut after the wrap is for the one case wrapping cannot
                # solve: a wide character in a one-column room. It is dropped
                # rather than allowed to push the line past its width.
                rows = [
                    truncate_row(line, text_width)
                    for r in rows
                    for line in wrap_row(r, text_width)
                ]

        rows = [[(ch, cell_pen.over(pen)) for ch, cell_pen in r] for r in rows]

        ws = self._whitespace_pen()
        if not p.inline:
            if pad_l or pad_r:
                rows = [blank(pad_l, ws) + r + blank(pad_r, ws) for r in rows]
            rows = [[] for _ in range(pad_t)] + rows + [[] for _ in range(pad_b)]

        if height > len(rows):
            gap = height - len(rows)
            above = _round(gap * p.align_v)
            rows = [[] for _ in range(above)] + rows + [[] for _ in range(gap - above)]

        inner = max([width] + [row_width(r) for r in rows])
        rows = [_pad_horizontal(r, inner, p.align_h, ws) for r in rows]
        if not p.inline:
            rows = self._apply_border(rows, inner)
            rows = self._apply_margins(rows)

        if p.max_width:
            rows = [truncate_row(r, p.max_width) for r in rows]
        if p.max_height:
            rows = rows[: p.max_height]
        full = max((row_width(r) for r in rows), default=0)
        return Block.from_rows(rows, min(full, p.max_width) if p.max_width else full)

    def _content(self, parts: Sequence[Content]) -> tuple[list[Row], bool]:
        if len(parts) == 1 and isinstance(parts[0], Block):
            return parts[0].rows(), True
        if any(isinstance(part, Block) for part in parts):
            raise TypeError(
                "a Block must be rendered on its own; use join_horizontal or "
                "join_vertical to set it beside other content"
            )
        cells: Row = []
        for i, part in enumerate(parts):
            if i:
                cells.append((" ", EMPTY))
            cells.extend(self._cells(part))
        rows: list[Row] = [[]]
        for cell in cells:
            if cell[0] == "\n":
                rows.append([])
            elif cell[0] != "\r":
                rows[-1].append(cell)
        return rows, False

    def _cells(self, part: str | Span | Sequence[Span]) -> Row:
        p = self._p
        if isinstance(part, str):
            part = [Span(part)]
        elif isinstance(part, Span):
            part = [part]
        spans = []
        for span in part:
            text = span.text
            if p.transform:
                text = p.transform(text)
            if p.tab_width >= 0:
                text = text.replace("\t", " " * p.tab_width)
            spans.append(Span(text, span.pen))
        return cells_of(spans)

    def _whitespace_pen(self) -> Pen:
        """The pen padding and alignment space are drawn with.

        Lip Gloss's: the background when whitespace is coloured, and with
        reverse on, the foreground and reverse too — otherwise reversed text
        would sit in un-reversed padding and the block would show a seam.
        """
        p = self._p
        pen = p.pen
        if pen.reverse:
            return Pen(fg=pen.fg, bg=pen.bg if p.color_whitespace else None, reverse=True)
        return Pen(bg=pen.bg) if p.color_whitespace and pen.bg else EMPTY

    def _apply_border(self, rows: list[Row], inner: int) -> list[Row]:
        top, right, bottom, left = self._active_sides()
        if not any((top, right, bottom, left)):
            return rows
        b = self._p.border
        fg, bg = self._p.border_fg, self._p.border_bg

        def ink(side: int) -> Pen:
            return Pen(fg=fg[side], bg=bg[side])

        left_glyph, right_glyph = b.left or " ", b.right or " "
        out: list[Row] = []
        if top:
            out.append(
                (to_row(b.top_left or " ", ink(0)) if left else [])
                + _edge(b.top or " ", inner, ink(0))
                + (to_row(b.top_right or " ", ink(0)) if right else [])
            )
        for r in rows:
            out.append(
                (to_row(left_glyph, ink(3)) if left else [])
                + r
                + (to_row(right_glyph, ink(1)) if right else [])
            )
        if bottom:
            out.append(
                (to_row(b.bottom_left or " ", ink(2)) if left else [])
                + _edge(b.bottom or " ", inner, ink(2))
                + (to_row(b.bottom_right or " ", ink(2)) if right else [])
            )
        return out

    def _apply_margins(self, rows: list[Row]) -> list[Row]:
        top, right, bottom, left = self._p.margin
        if not any((top, right, bottom, left)):
            return rows
        pen = Pen(bg=self._p.margin_bg) if self._p.margin_bg else EMPTY
        rows = [blank(left, pen) + r + blank(right, pen) for r in rows]
        full = max((row_width(r) for r in rows), default=left + right)
        return (
            [blank(full, pen) for _ in range(top)]
            + rows
            + [blank(full, pen) for _ in range(bottom)]
        )


def _edge(glyph: str, width: int, pen: Pen) -> Row:
    """*glyph* repeated to exactly *width* columns."""
    unit = to_row(glyph, pen)
    unit_width = row_width(unit) or 1
    row: Row = unit * (width // unit_width)
    return row + blank(width - row_width(row), pen)


def _round(x: float) -> int:
    import math

    return int(math.floor(x + 0.5))
