"""Bubbles' drawn parts: help line, progress bar, paginator, scrollbar, list rows.

These are the *drawing* halves of Bubbles' components. Bubbles' own
components also hold state and handle keys; here the app keeps the state
(which row is selected, how far it has scrolled, what percent is done) and
passes it in, and every function returns a :class:`~bewitch.lipgloss.Block`
exactly as wide as it was asked for — never a column more, so a phone at
40 columns never wraps a line it was promised would fit.

Colours come from a :class:`~bewitch.theme.Theme`, by role, defaulting to
Crush's (:data:`~bewitch.theme.CHARM`).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from bewitch import glyphs
from bewitch.color import Color
from bewitch.lipgloss import Block, Pen, Span, blend_1d, string_width
from bewitch.lipgloss._cells import Row, blank, cells_of, row_width, to_row, truncate_row
from bewitch.theme import CHARM, Theme


def _block(row: Row, width: int) -> Block:
    return Block.from_rows([truncate_row(row, width)], width)


# Help ------------------------------------------------------------------------


def short_help(
    bindings: Sequence[tuple[str, str]],
    width: int,
    theme: Theme = CHARM,
    separator: str | Sequence[str] = (" • ", "  "),
) -> Block:
    """``key desc • key desc``, as Bubbles' ``ShortHelpView`` draws it.

    *separator* may be several, tried in order: the first that lets every
    pair fit is used. The default tries Bubbles' `` • `` and then two plain
    spaces, because on a phone the dot is what goes before a key does — a
    hint line missing its last pair is usually missing the way out.

    If no separator fits them all, pairs are added whole until the next would
    not fit; then, if there is room, an ellipsis says some were left out —
    the same rule as Bubbles, so a hint is never shown cut in half. Keys are
    a shade lighter than their descriptions, and the separator quieter than
    both, as in Crush.
    """
    options = [separator] if isinstance(separator, str) else list(separator)
    for sep in options:
        row, complete = _help_row(bindings, width, theme, sep)
        if complete:
            return _block(row, width)
    return _block(row, width)


def _help_row(
    bindings: Sequence[tuple[str, str]], width: int, theme: Theme, separator: str
) -> tuple[Row, bool]:
    key_pen = Pen(fg=theme.fg_more_subtle)
    desc_pen = Pen(fg=theme.fg_most_subtle)
    sep_pen = Pen(fg=theme.separator)
    row: Row = []
    used = 0
    for i, (key, desc) in enumerate(bindings):
        item = (to_row(separator, sep_pen) if i else []) + to_row(key, key_pen)
        if desc:
            item += to_row(" " + desc, desc_pen)
        w = row_width(item)
        if used + w > width:
            tail = to_row(" " + glyphs.ELLIPSIS, sep_pen)
            if used + row_width(tail) < width:
                row += tail
            return row, False
        row += item
        used += w
    return row, True


# Progress --------------------------------------------------------------------


def progress_bar(
    percent: float,
    width: int,
    theme: Theme = CHARM,
    show_percentage: bool = True,
    stops: Sequence[Color] | None = None,
) -> Block:
    """A filled bar running through *stops* (primary → secondary), then
    the empty part, then the percentage.

    Like Bubbles' blended bar, the gradient is laid across the whole width
    and the filled part shows as much of it as it has reached, so the colour
    at a given column never changes as the bar fills.
    """
    percent = min(1.0, max(0.0, percent))
    label = f" {round(percent * 100):3d}%" if show_percentage else ""
    track = max(0, width - string_width(label))
    filled = min(track, max(0, int(math.floor(track * percent + 0.5))))
    ramp = blend_1d(track, *(stops or (theme.primary, theme.secondary)))
    row: Row = [(glyphs.BAR_FULL, Pen(fg=ramp[i])) for i in range(filled)]
    row += to_row(glyphs.BAR_EMPTY * (track - filled), Pen(fg=theme.fg_most_subtle))
    row += to_row(label, Pen(fg=theme.fg_more_subtle))
    return _block(row, width)


# Paginator -------------------------------------------------------------------


def paginator_dots(page: int, pages: int, theme: Theme = CHARM) -> Block:
    """``• ○ ○``: Bubbles' dots paginator, the current page filled."""
    row: Row = []
    for i in range(pages):
        if i == page:
            row += to_row("•", Pen(fg=theme.fg_base))
        else:
            row += to_row("○", Pen(fg=theme.fg_most_subtle))
    return Block.from_rows([row])


# Scrollbar -------------------------------------------------------------------


def scroll_thumb(height: int, total: int, visible: int, offset: int) -> tuple[int, int]:
    """Where the thumb goes: ``(start, length)`` in rows of a *height* track.

    The thumb is at least one row, as long as the visible share of the list,
    and reaches the bottom exactly when the last row is showing.
    """
    if height <= 0:
        return (0, 0)
    if total <= visible or total <= 0:
        return (0, height)
    length = max(1, min(height, int(math.floor(height * visible / total + 0.5))))
    furthest = max(1, total - visible)
    offset = min(max(0, offset), furthest)
    start = int(math.floor((height - length) * offset / furthest + 0.5))
    return (start, length)


def scrollbar(
    height: int, total: int, visible: int, offset: int, theme: Theme = CHARM
) -> Block:
    """A one-column scrollbar: Crush's ``┃`` thumb on a quiet ``│`` track."""
    start, length = scroll_thumb(height, total, visible, offset)
    thumb = Pen(fg=theme.secondary)
    track = Pen(fg=theme.separator)
    return Block.from_rows(
        [
            to_row(glyphs.SCROLL_THUMB, thumb)
            if start <= i < start + length
            else to_row(glyphs.SCROLL_TRACK, track)
            for i in range(height)
        ],
        1,
    )


# List rows -------------------------------------------------------------------


def list_item(
    title: str | Sequence[Span],
    width: int,
    subtitle: str | Sequence[Span] | None = None,
    selected: bool = False,
    mark: str = "",
    mark_color: Color | None = None,
    dimmed: bool = False,
    theme: Theme = CHARM,
) -> Block:
    """One list entry, one or two lines, exactly *width* columns.

    Selected, the whole entry is a filled bar in the primary colour — Crush's
    selection, never reverse video. *mark* is a one-column glyph in front of
    the title (``✓`` for "already have it"), drawn in *mark_color*; the
    column is kept even with no mark, so marking an entry never shifts its
    title. *dimmed* draws the entry a step back, for things already dealt
    with. Titles and subtitles too long for the row end in ``…``.
    """
    if selected:
        base = Pen(fg=theme.on_primary, bg=theme.primary)
        sub = Pen(fg=theme.fg_subtle, bg=theme.primary)
        fill = Pen(bg=theme.primary)
    else:
        base = Pen(fg=theme.fg_more_subtle if dimmed else theme.fg_base)
        sub = Pen(fg=theme.fg_most_subtle if dimmed else theme.fg_more_subtle)
        fill = Pen()

    def text_row(content: str | Sequence[Span], pen: Pen) -> Row:
        spans = [Span(content)] if isinstance(content, str) else list(content)
        return [(ch, p.over(pen)) for ch, p in cells_of(spans)]

    room = max(0, width - 4)  # pad, mark, space … pad
    ellipsis = to_row(glyphs.ELLIPSIS, base)
    mark_pen = Pen(fg=mark_color).over(fill) if mark_color else base
    head = blank(1, fill) + to_row((mark or " ")[:1], mark_pen) + blank(1, fill)
    rows = [head + truncate_row(text_row(title, base), room, ellipsis)]
    if subtitle is not None:
        rows.append(
            blank(3, fill)
            + truncate_row(text_row(subtitle, sub), room, to_row(glyphs.ELLIPSIS, sub))
        )
    return Block.from_rows(
        [
            truncate_row(r, width)
            + blank(width - row_width(truncate_row(r, width)), fill)
            for r in rows
        ],
        width,
    )


__all__ = [
    "list_item",
    "paginator_dots",
    "progress_bar",
    "scroll_thumb",
    "scrollbar",
    "short_help",
]
