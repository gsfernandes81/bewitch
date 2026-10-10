"""Border sets, as Lip Gloss defines them.

The same sets with the same glyphs, as functions named after Lip Gloss's
(``NormalBorder()`` is :func:`normal_border`). Every glyph here except
``double_border``'s was drawn at one column on the phone this was written
for; double is kept because Lip Gloss has it, not because Crush uses it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Border:
    top: str = ""
    bottom: str = ""
    left: str = ""
    right: str = ""
    top_left: str = ""
    top_right: str = ""
    bottom_left: str = ""
    bottom_right: str = ""
    middle_left: str = ""
    middle_right: str = ""
    middle: str = ""
    middle_top: str = ""
    middle_bottom: str = ""


def _set(edges: str, corners: str, middles: str = "") -> Border:
    t, b, lft, r = edges
    tl, tr, bl, br = corners
    ml, mr, m, mt, mb = middles or "     "
    return Border(t, b, lft, r, tl, tr, bl, br, ml, mr, m, mt, mb)


def no_border() -> Border:
    return Border()


def normal_border() -> Border:
    return _set("──││", "┌┐└┘", "├┤┼┬┴")


def rounded_border() -> Border:
    """Crush's dialogs. The softer corner is most of the Charm look."""
    return _set("──││", "╭╮╰╯", "├┤┼┬┴")


def block_border() -> Border:
    return _set("████", "████", "█████")


def outer_half_block_border() -> Border:
    return _set("▀▄▌▐", "▛▜▙▟")


def inner_half_block_border() -> Border:
    return _set("▄▀▐▌", "▗▖▝▘")


def thick_border() -> Border:
    return _set("━━┃┃", "┏┓┗┛", "┣┫╋┳┻")


def double_border() -> Border:
    return _set("══║║", "╔╗╚╝", "╠╣╬╦╩")


def hidden_border() -> Border:
    """Takes the room a border would, draws nothing."""
    return _set("    ", "    ", "     ")


def markdown_border() -> Border:
    return _set("--||", "||||", "|||||")


def ascii_border() -> Border:
    """For a terminal that cannot draw box glyphs at all."""
    return _set("--||", "++++", "+++++")
