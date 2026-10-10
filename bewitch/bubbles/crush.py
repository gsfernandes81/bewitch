"""Crush's own pieces: the header band, section rules, dialog titles, labels.

Bubbles has no header or section component — these are how Crush lays out
its screens, and they are most of what makes a screen read as Charm's at a
glance. They are written here from how Crush *looks* (Crush is FSL-licensed;
see THIRD_PARTY.md): the ``╱`` band after the name, a grey title running into
a ``─`` rule, a dialog title trailing a violet-to-pink band, a word on a
coloured background.

Every function returns a :class:`~bewitch.lipgloss.Block` exactly *width*
columns wide, and gives up decoration before it gives up words: the band
shrinks before the details are cut, and the details are cut before the name.
"""

from __future__ import annotations

from collections.abc import Sequence

from bewitch import glyphs
from bewitch.lipgloss import Block, Pen, Span, foreground_gradient
from bewitch.lipgloss._cells import Row, blank, cells_of, row_width, to_row, truncate_row
from bewitch.theme import CHARM, Theme

#: The fewest diagonals a header band is drawn with; below this the details
#: are cut instead, as in Crush.
MIN_DIAGONALS = 3


def _row(spans: Sequence[Span]) -> Row:
    return cells_of(spans)


def _exact(row: Row, width: int) -> Block:
    row = truncate_row(row, width)
    return Block.from_rows([row + blank(width - row_width(row))], width)


def header(
    name: str,
    details: Sequence[str] = (),
    width: int = 40,
    theme: Theme = CHARM,
) -> Block:
    """`` name ╱╱╱╱╱╱ detail • detail``: Crush's top line.

    The name is bold, in a gradient from secondary to primary; the band is
    primary; details are muted with quiet ``•`` separators. The band takes
    what the name and details leave, never fewer than
    :data:`MIN_DIAGONALS`; when the details will not fit beside that they
    are cut with ``…``, and when even the name will not, only the name is
    shown.
    """
    logo = foreground_gradient(name, theme.secondary, theme.primary, pen=Pen(bold=True))
    dot = to_row(" • ", Pen(fg=theme.fg_most_subtle))
    info: Row = []
    for i, d in enumerate(details):
        info += (dot if i else []) + to_row(d, Pen(fg=theme.fg_more_subtle))

    lead = blank(1) + _row(logo) + blank(1)
    room = width - row_width(lead) - 1  # one column of right padding
    band_pen = Pen(fg=theme.primary)
    if room < MIN_DIAGONALS:
        return _exact(lead, width)
    if info:
        info_room = room - MIN_DIAGONALS - 1
        if info_room < 1:
            info = []
        else:
            info = truncate_row(
                info, info_room, to_row(glyphs.ELLIPSIS, Pen(fg=theme.fg_more_subtle))
            )
    band = room - (row_width(info) + 1 if info else 0)
    row = lead + to_row(glyphs.DIAGONAL * band, band_pen)
    if info:
        row += blank(1) + info
    return _exact(row, width)


def section(
    title: str,
    width: int,
    info: str | None = None,
    theme: Theme = CHARM,
) -> Block:
    """``Title ──────── info``: a grey title running into a quiet rule.

    The rule fills whatever the title and *info* leave; *info* is dropped
    before the title is cut.
    """
    title_row = to_row(title, Pen(fg=theme.fg_most_subtle))
    info_row = to_row(info, Pen(fg=theme.fg_most_subtle)) if info else []
    rule_pen = Pen(fg=theme.separator)
    rule = width - row_width(title_row) - 1 - (row_width(info_row) + 1 if info_row else 0)
    if info_row and rule < 1:
        info_row, rule = [], width - row_width(title_row) - 1
    if rule < 1:
        return _exact(
            truncate_row(
                title_row, width, to_row(glyphs.ELLIPSIS, Pen(fg=theme.fg_most_subtle))
            ),
            width,
        )
    row = title_row + blank(1) + to_row(glyphs.SECTION * rule, rule_pen)
    if info_row:
        row += blank(1) + info_row
    return _exact(row, width)


def dialog_title(title: str, width: int, theme: Theme = CHARM) -> Block:
    """``Title ╱╱╱╱╱╱``: a dialog's title, trailing a primary→secondary band."""
    title_row = to_row(title, Pen(fg=theme.primary))
    if row_width(title_row) > width:
        return _exact(
            truncate_row(
                title_row, width, to_row(glyphs.ELLIPSIS, Pen(fg=theme.primary))
            ),
            width,
        )
    room = width - row_width(title_row) - 1
    band = foreground_gradient(glyphs.DIAGONAL * room, theme.primary, theme.secondary)
    return _exact(title_row + (blank(1) + _row(band) if room > 0 else []), width)


#: label kind → (background role, foreground role, bold)
_TAGS = {
    "error": ("destructive", "on_primary", False),
    "warn": ("attention", "bg_base", True),
    "info": ("info", "on_primary", False),
    "success": ("success", "bg_base", True),
    "primary": ("primary", "on_primary", False),
}


def tag(text: str, kind: str = "info", theme: Theme = CHARM) -> Block:
    """`` TEXT ``: a word on a coloured background, padded one each side.

    *kind* is ``error``, ``warn``, ``info``, ``success`` or ``primary``. A
    label is never the only thing saying what it says: its text is the
    signal, the colour only makes it quicker to see.
    """
    bg, fg, bold = _TAGS[kind]
    pen = Pen(fg=getattr(theme, fg), bg=getattr(theme, bg), bold=bold or None)
    return Block.from_rows([to_row(f" {text} ", pen)])


def status(
    icon: str,
    title: str,
    width: int,
    description: str = "",
    icon_color=None,
    theme: Theme = CHARM,
) -> Block:
    """``● Title description``: Crush's status row. The description is cut
    with ``…`` to fit; the icon and title are not."""
    row = to_row(icon, Pen(fg=icon_color or theme.fg_more_subtle)) + blank(1)
    row += to_row(title, Pen(fg=theme.fg_more_subtle))
    if description:
        room = width - row_width(row) - 1
        if room > 1:
            row += blank(1) + truncate_row(
                to_row(description, Pen(fg=theme.fg_most_subtle)),
                room,
                to_row(glyphs.ELLIPSIS, Pen(fg=theme.fg_most_subtle)),
            )
    return _exact(row, width)
