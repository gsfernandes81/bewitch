"""The ANSI adapter: a Block written as escape sequences, for ``print()``.

This is the adapter for anything that takes a string with SGR sequences in
it — a plain terminal, blessed (which passes them straight through), Rich's
``Text.from_ansi``. Curses is the one that does not, and gets an adapter of
its own.

Each line stands alone: it opens with whatever its first span needs and ends
with a reset, so a line can be drawn anywhere — at a cursor position, after
a ``clear`` — without inheriting the colour the previous line ended on.
Under :attr:`Profile.NO_TTY` nothing but the text is written at all.

One rule is this adapter's own: **under :attr:`Profile.ASCII` a background
becomes reverse video.** A filled selection bar is a background, and with
colour stripped it would vanish, leaving a list with no visible cursor —
the one thing on the screen that must never depend on colour alone. Reverse
video is what every terminal since the VT100 can draw, and what the bar
stood for anyway.
"""

from __future__ import annotations

from bewitch.color import Color
from bewitch.colorprofile import Indexed, Profile, convert, detect
from bewitch.lipgloss._cells import Block, Pen, Span

RESET = "\x1b[0m"


def render(block: Block, profile: Profile | None = None) -> str:
    """*block* as text with escape sequences, lines joined with ``\\n``.

    *profile* defaults to what stdout supports (:func:`colorprofile.detect`).
    """
    profile = detect() if profile is None else profile
    return "\n".join(line(spans, profile) for spans in block.lines)


def line(spans: tuple[Span, ...], profile: Profile) -> str:
    """One line of spans, self-contained: it resets at its end."""
    if profile == Profile.NO_TTY:
        return "".join(s.text for s in spans)
    out: list[str] = []
    current = ""
    for span in spans:
        codes = sgr(span.pen, profile)
        if codes != current:
            out.append(RESET if not codes else f"\x1b[0;{codes}m")
            current = codes
        out.append(span.text)
    if current:
        out.append(RESET)
    return "".join(out)


def sgr(pen: Pen, profile: Profile) -> str:
    """The SGR parameters for *pen* under *profile*, ``""`` for none."""
    if profile == Profile.NO_TTY:
        return ""
    codes: list[str] = []
    if pen.bold:
        codes.append("1")
    if pen.faint:
        codes.append("2")
    if pen.italic:
        codes.append("3")
    if pen.underline:
        codes.append("4")
    reverse = bool(pen.reverse)
    if profile == Profile.ASCII and pen.bg is not None:
        reverse = not reverse
    if reverse:
        codes.append("7")
    if pen.strikethrough:
        codes.append("9")
    fg = _color(pen.fg, profile, background=False)
    bg = _color(pen.bg, profile, background=True)
    return ";".join(codes + [c for c in (fg, bg) if c])


def _color(color: Color | None, profile: Profile, background: bool) -> str:
    fitted = convert(color, profile)
    if fitted is None:
        return ""
    if isinstance(fitted, Indexed):
        n = fitted.n
        if profile == Profile.ANSI:
            base = (40 if background else 30) if n < 8 else (100 if background else 90)
            return str(base + n % 8)
        return f"{48 if background else 38};5;{n}"
    return f"{48 if background else 38};2;{fitted.r};{fitted.g};{fitted.b}"
