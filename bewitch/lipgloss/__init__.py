"""A Python port of Charm's Lip Gloss: style definitions for terminal layouts.

Follows ``charm.land/lipgloss/v2`` v2.0.6. Names are Lip Gloss's in Python
spelling, so Lip Gloss's own documentation reads across::

    Go                                   bewitch
    lipgloss.NewStyle().Bold(true)       Style().bold()
    lipgloss.RoundedBorder()             rounded_border()
    lipgloss.JoinHorizontal(Top, a, b)   join_horizontal(TOP, a, b)
    lipgloss.Width(s)                    width(s)
    lipgloss.Blend1D(10, a, b)           blend_1d(10, a, b)

The one thing that is not a straight port is what a render *is*: a
:class:`Block` of styled spans, not a string full of escape sequences. See
``_cells.py`` for why; ``str(block)`` gives you the string.

``Canvas`` is Lip Gloss v2's canvas without its layers and hit-testing:
compose blocks at a position, later over earlier.

Not ported (yet): Lip Gloss's ``table``, ``list`` and ``tree`` sub-packages,
hyperlinks, underline styles and colours, and ``Blend2D``.
"""

from bewitch.lipgloss._cells import (
    EMPTY,
    Block,
    Pen,
    Span,
    char_width,
    height,
    string_width,
    truncate,
    width,
)
from bewitch.lipgloss.blending import blend_1d, foreground_gradient
from bewitch.lipgloss.canvas import Canvas
from bewitch.lipgloss.borders import (
    Border,
    ascii_border,
    block_border,
    double_border,
    hidden_border,
    inner_half_block_border,
    markdown_border,
    no_border,
    normal_border,
    outer_half_block_border,
    rounded_border,
    thick_border,
)
from bewitch.lipgloss.join import (
    BOTTOM,
    CENTER,
    LEFT,
    RIGHT,
    TOP,
    Position,
    join_horizontal,
    join_vertical,
    place,
    place_horizontal,
    place_vertical,
)
from bewitch.lipgloss.style import Style

__all__ = [
    "BOTTOM",
    "CENTER",
    "EMPTY",
    "LEFT",
    "RIGHT",
    "TOP",
    "Block",
    "Border",
    "Canvas",
    "Pen",
    "Position",
    "Span",
    "Style",
    "ascii_border",
    "blend_1d",
    "block_border",
    "char_width",
    "double_border",
    "foreground_gradient",
    "height",
    "hidden_border",
    "inner_half_block_border",
    "join_horizontal",
    "join_vertical",
    "markdown_border",
    "no_border",
    "normal_border",
    "outer_half_block_border",
    "place",
    "place_horizontal",
    "place_vertical",
    "rounded_border",
    "string_width",
    "thick_border",
    "truncate",
    "width",
]
