"""The glyphs Crush draws with, each with an ASCII stand-in.

Every glyph here was drawn on the phone this package was written for
(Termux, 2026-10-10) and came out one column wide, in the terminal's own
font, with every right edge still lined up. Three Crush glyphs did not, and
are left out on purpose — do not add them back without trying them on a
phone first:

* ``⏸`` (Crush's plan-mode icon) — Android draws it as an orange emoji. It
  keeps to one column, but ignores the colour it is given.
* ``✕`` (Crush's "remove") — not in the terminal font; a fallback font's
  larger X arrives in its place. Use :data:`ERROR` (``×``) instead.
* ``⟳`` (Crush's "loading") — also borrowed from a fallback font, small and
  off-centre. A spinner says "working" better anyway.

Use :func:`pick` rather than the constants when a screen may be drawn where
box-drawing characters are not available (``TERM=dumb``, a serial console):
it gives the ASCII stand-in when asked to.
"""

from __future__ import annotations

# name: (glyph, ascii)
GLYPHS: dict[str, tuple[str, str]] = {
    "check": ("✓", "v"),
    "error": ("×", "x"),
    "pending": ("●", "*"),
    "radio_on": ("◉", "(*)"),
    "radio_off": ("○", "( )"),
    "bullet": ("•", "*"),
    "dot": ("·", "."),
    "ellipsis": ("…", "..."),
    "arrow_right": ("→", "->"),
    "arrow_up": ("↑", "^"),
    "arrow_down": ("↓", "v"),
    "arrow_left": ("←", "<"),
    "enter": ("⏎", "enter"),
    "model": ("◇", "<>"),
    "credit": ("◆", "<>"),
    "thinking": ("⋯", "..."),
    "image": ("■", "#"),
    "text": ("≡", "="),
    "skill": ("▲", "^"),
    "diagonal": ("╱", "/"),
    "section": ("─", "-"),
    "border_thin": ("│", "|"),
    "border_thick": ("▌", "|"),
    "scroll_thumb": ("┃", "#"),
    "scroll_track": ("│", "|"),
    "bar_full": ("█", "#"),
    "bar_empty": ("░", "."),
}

CHECK = GLYPHS["check"][0]
ERROR = GLYPHS["error"][0]
PENDING = GLYPHS["pending"][0]
RADIO_ON = GLYPHS["radio_on"][0]
RADIO_OFF = GLYPHS["radio_off"][0]
BULLET = GLYPHS["bullet"][0]
DOT = GLYPHS["dot"][0]
ELLIPSIS = GLYPHS["ellipsis"][0]
ARROW_RIGHT = GLYPHS["arrow_right"][0]
ENTER = GLYPHS["enter"][0]
MODEL = GLYPHS["model"][0]
CREDIT = GLYPHS["credit"][0]
THINKING = GLYPHS["thinking"][0]
DIAGONAL = GLYPHS["diagonal"][0]
SECTION = GLYPHS["section"][0]
BORDER_THIN = GLYPHS["border_thin"][0]
BORDER_THICK = GLYPHS["border_thick"][0]
SCROLL_THUMB = GLYPHS["scroll_thumb"][0]
SCROLL_TRACK = GLYPHS["scroll_track"][0]
BAR_FULL = GLYPHS["bar_full"][0]
BAR_EMPTY = GLYPHS["bar_empty"][0]

#: Crush glyphs that failed on the phone. Kept as data so a test can hold
#: the line: none of these may appear in a recipe.
EXCLUDED: dict[str, str] = {
    "⏸": "drawn as a coloured emoji on Android",
    "✕": "missing from the terminal font; a fallback font's glyph is used",
    "⟳": "missing from the terminal font; small and off-centre",
}


def pick(name: str, ascii_only: bool = False) -> str:
    """The glyph called *name*, or its ASCII stand-in."""
    glyph, fallback = GLYPHS[name]
    return fallback if ascii_only else glyph
