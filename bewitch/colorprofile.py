"""How much colour the terminal can show, and how to fit a colour to it.

A port of Charm's ``colorprofile`` (v0.4.3) with the colour arithmetic of
``x/ansi`` behind it. Detection reads the environment the way colorprofile
does, with three changes, each named where it is made:

* **Termux is truecolor.** Termux sets ``TERM=xterm-256color`` and, on the
  phone this was written for, no ``COLORTERM`` — so colorprofile's rules
  read it as 256 colours, while the terminal draws 24-bit colour perfectly
  (checked on the device, 2026-10-10). ``TERMUX_VERSION`` is set by every
  Termux session, so it is the tell.
* **``BEWITCH_COLOR`` wins over everything** — ``truecolor``, ``256``,
  ``16``, ``ascii`` or ``none`` — because a guess about a terminal is
  sometimes wrong and the person in front of it is not.
* **No terminfo or tmux queries.** colorprofile also reads the terminfo
  database and asks a running tmux; neither is worth a subprocess at import
  time here, and ``BEWITCH_COLOR`` covers the cases they would catch.

Conversion follows ``x/ansi``'s ``Convert256``, itself ported from tmux:
snap to the 6x6x6 cube, work out the nearest grey, keep whichever is nearer.
Where x/ansi measures "nearer" in HSLuv this measures it in CIELAB (ΔE76) —
the same idea, a colour space this package already carries for blending.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import IO

from bewitch.color import Color


class Profile(IntEnum):
    """Ordered from least to most capable, as colorprofile orders them."""

    #: Not a terminal: no escape sequences at all.
    NO_TTY = 0
    #: A terminal, but no colour: attributes (bold, faint…) only.
    ASCII = 1
    #: The 16 basic colours.
    ANSI = 2
    #: The 256-colour palette.
    ANSI256 = 3
    #: 24-bit colour.
    TRUE_COLOR = 4


@dataclass(frozen=True, slots=True)
class Indexed:
    """A palette colour: 0-15 basic, 16-231 the cube, 232-255 the greys."""

    n: int

    def __post_init__(self) -> None:
        if not 0 <= self.n <= 255:
            raise ValueError(f"palette index out of range 0-255: {self.n}")


_OVERRIDES = {
    "truecolor": Profile.TRUE_COLOR,
    "24bit": Profile.TRUE_COLOR,
    "256": Profile.ANSI256,
    "16": Profile.ANSI,
    "ascii": Profile.ASCII,
    "none": Profile.NO_TTY,
}


def detect(
    stream: IO[str] | None = None, env: Mapping[str, str] | None = None
) -> Profile:
    """The profile for writing to *stream* (stdout) under *env* (os.environ)."""
    env = os.environ if env is None else env
    stream = sys.stdout if stream is None else stream
    try:
        isatty = stream.isatty()
    except (AttributeError, ValueError):
        isatty = False
    return env_profile(env, isatty=isatty or _truthy(env.get("TTY_FORCE")))


def env_profile(env: Mapping[str, str], isatty: bool = True) -> Profile:
    """What *env* says, for output that is (or is not) a terminal."""
    override = env.get("BEWITCH_COLOR", "").strip().lower()
    if override in _OVERRIDES:
        return _OVERRIDES[override]

    term = env.get("TERM", "")
    dumb = term in ("", "dumb")
    envp = _env_color_profile(env)
    profile = Profile.NO_TTY if (not isatty or dumb) else envp

    if _truthy(env.get("NO_COLOR")) and isatty:
        return min(profile, Profile.ASCII)
    if _truthy(env.get("CLICOLOR_FORCE")):
        return max(profile, Profile.ANSI, envp)
    if _truthy(env.get("CLICOLOR")) and isatty and not dumb:
        return max(profile, Profile.ANSI)
    return profile


def _env_color_profile(env: Mapping[str, str]) -> Profile:
    term = env.get("TERM", "")
    profile = Profile.NO_TTY if term in ("", "dumb") else Profile.ANSI

    if env.get("TERMUX_VERSION"):
        return Profile.TRUE_COLOR
    # colorprofile's list, kept as written: "st" is a substring test there too.
    if any(
        name in term
        for name in (
            "alacritty",
            "contour",
            "foot",
            "ghostty",
            "kitty",
            "rio",
            "st",
            "wezterm",
        )
    ):
        return Profile.TRUE_COLOR
    if term.startswith(("tmux", "screen")):
        profile = max(profile, Profile.ANSI256)
    elif term.startswith("xterm"):
        profile = max(profile, Profile.ANSI)
    if env.get("WT_SESSION") or _truthy(env.get("GOOGLE_CLOUD_SHELL")):
        return Profile.TRUE_COLOR
    colorterm = env.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit", "yes", "true") and not term.startswith(
        ("screen", "tmux")
    ):
        return Profile.TRUE_COLOR
    if term.endswith("256color"):
        profile = max(profile, Profile.ANSI256)
    if term.endswith("direct"):
        return Profile.TRUE_COLOR
    return profile


def _truthy(value: str | None) -> bool:
    # Go's strconv.ParseBool, which is what colorprofile reads these with.
    return (value or "").strip() in ("1", "t", "T", "TRUE", "true", "True")


def convert(color: Color | Indexed | None, profile: Profile) -> Color | Indexed | None:
    """*color* fitted to *profile*: unchanged, a palette index, or nothing."""
    if color is None or profile <= Profile.ASCII:
        return None
    if profile == Profile.TRUE_COLOR:
        return color
    if isinstance(color, Indexed):
        return color if profile == Profile.ANSI256 else _to_16(color)
    if profile == Profile.ANSI256:
        return convert_256(color)
    return _to_16(convert_256(color))


_CUBE = (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)


def _to_6cube(v: int) -> int:
    # tmux's colour_to_6cube.
    if v < 48:
        return 0
    if v < 115:
        return 1
    return (v - 35) // 40


def convert_256(color: Color) -> Indexed:
    """The nearest of the 256 palette colours to *color*."""
    qr, qg, qb = _to_6cube(color.r), _to_6cube(color.g), _to_6cube(color.b)
    cube = Color(_CUBE[qr], _CUBE[qg], _CUBE[qb])
    index = 36 * qr + 6 * qg + qb
    if cube == color:
        return Indexed(16 + index)

    average = (color.r + color.g + color.b) // 3
    # Go's integer division truncates toward zero; Python's // floors, and
    # for an average under 3 the two disagree. int() of the true quotient is
    # Go's answer.
    grey_index = 23 if average > 238 else int((average - 3) / 10)
    grey = 8 + 10 * grey_index
    if color.distance(cube) <= color.distance(Color(grey, grey, grey)):
        return Indexed(16 + index)
    return Indexed(232 + grey_index)


def palette_color(index: Indexed) -> Color:
    """The RGB a standard xterm palette shows for *index*."""
    n = index.n
    if n < 16:
        return _BASIC[n]
    if n < 232:
        n -= 16
        return Color(_CUBE[n // 36], _CUBE[(n // 6) % 6], _CUBE[n % 6])
    grey = 8 + 10 * (n - 232)
    return Color(grey, grey, grey)


#: xterm's default 16, the values x/ansi's table starts with.
_BASIC = tuple(
    Color.parse(h)
    for h in (
        "#000000",
        "#800000",
        "#008000",
        "#808000",
        "#000080",
        "#800080",
        "#008080",
        "#c0c0c0",
        "#808080",
        "#ff0000",
        "#00ff00",
        "#ffff00",
        "#0000ff",
        "#ff00ff",
        "#00ffff",
        "#ffffff",
    )
)


def _to_16(index: Indexed) -> Indexed:
    # x/ansi carries a hand-made 256→16 table; this computes the same kind of
    # answer — the nearest basic colour — rather than copying 240 numbers.
    if index.n < 16:
        return index
    return _NEAREST_16[index.n - 16]


def _nearest_basic(n: int) -> Indexed:
    color = palette_color(Indexed(n))
    return Indexed(min(range(16), key=lambda b: color.distance(_BASIC[b])))


_NEAREST_16 = tuple(_nearest_basic(n) for n in range(16, 256))
