"""huh's look: how Charm's huh marks an option, as a recipe.

Follows the Charm theme (``ThemeCharm``) of
`huh <https://github.com/charmbracelet/huh>`_ v2.0.3, which marks a ticked
option ``✓`` in green and an unticked one ``•`` in grey. Like the rest of
:mod:`bewitch.bubbles` this is the drawing half only: the app holds whether
a box is ticked and flips it on a key or a tap; bewitch draws what it is
told, exactly as wide as it is told.
"""

from __future__ import annotations

from bewitch import glyphs
from bewitch.lipgloss import CENTER, Block, Pen, Style, rounded_border
from bewitch.lipgloss._cells import Row, blank, row_width, to_row, truncate_row
from bewitch.theme import CHARM, Theme


def _mark(label: str, checked: bool, width: int, theme: Theme) -> Row:
    """``✓ label`` or ``• label`` in at most *width* columns: the label is
    cut with ``…``, and dropped, before the glyph is."""
    if width < 1:
        return []
    if checked:
        row = to_row(glyphs.CHECK, Pen(fg=theme.success))
        pen = Pen(fg=theme.fg_base, bold=True)
    else:
        row = to_row(glyphs.BULLET, Pen(fg=theme.fg_most_subtle))
        pen = Pen(fg=theme.fg_more_subtle)
    if label and width >= 3:
        text = truncate_row(to_row(label, pen), width - 2, to_row(glyphs.ELLIPSIS, pen))
        row += blank(1) + text
    return row


def checkbox(
    label: str,
    checked: bool,
    width: int,
    boxed: bool = False,
    theme: Theme = CHARM,
) -> Block:
    """``✓ label`` / ``• label``, exactly *width* columns.

    Ticked, the ``✓`` is in ``success`` and the label bold in ``fg_base``;
    unticked, the ``•`` is in ``fg_most_subtle`` and the label in
    ``fg_more_subtle``. With colour gone the glyph and the bold weight still
    say which it is. Both glyphs take the same column, so ticking never
    shifts the label.

    *boxed* draws it as a three-row tap target, the height of a button: a
    rounded border in ``success`` when ticked and ``fg_most_subtle`` when
    not, the mark and label centred inside. Too narrow for a border, the
    border goes and the mark sits on the middle row, still three rows tall.
    """
    if not boxed:
        row = _mark(label, checked, width, theme)
        return Block.from_rows([row + blank(width - row_width(row))], width)
    inner = width - 2
    if inner < 1:
        row = _mark(label, checked, width, theme)
        row += blank(width - row_width(row))
        return Block.from_rows([blank(width), row, blank(width)], width)
    pad = 1 if inner >= 3 else 0
    content = _mark(label, checked, inner - 2 * pad, theme)
    edge = theme.success if checked else theme.fg_most_subtle
    return (
        Style()
        .border(rounded_border())
        .border_foreground(edge)
        .padding(0, pad)
        .width(width)
        .align(CENTER)
        .render(Block.from_rows([content]))
    )


__all__ = ["checkbox"]
