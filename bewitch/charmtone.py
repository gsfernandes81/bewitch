"""The CharmTone palette, ported from Charm's ``charmtone``.

Follows ``github.com/charmbracelet/x/exp/charmtone`` v0.1.0: the same 70
colours, the same names, the same order, and the same groups. Names are kept
exactly as Charm spells them (``charmtone.Charple``) rather than shouted into
Python constant case, so Charm's own documentation reads straight across.

Each tone is a :class:`~bewitch.color.Color` that also knows its name. The
values are generated from the Go source; edit that, not this, when Charm
changes a colour.
"""

from __future__ import annotations

from dataclasses import dataclass

from bewitch.color import Color


@dataclass(frozen=True, slots=True, eq=False)
class Tone(Color):
    """A CharmTone colour: a :class:`Color` with the name Charm gave it."""

    name: str = ""

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"charmtone.{self.name}"


# fmt: off
Cumin = Tone(0xBF, 0x97, 0x6F, "Cumin")
Tang = Tone(0xFF, 0x98, 0x5A, "Tang")
Yam = Tone(0xFF, 0xB5, 0x87, "Yam")
Paprika = Tone(0xD3, 0x6C, 0x64, "Paprika")
Bengal = Tone(0xFF, 0x6E, 0x63, "Bengal")
Uni = Tone(0xFF, 0x93, 0x7D, "Uni")
Sriracha = Tone(0xEB, 0x42, 0x68, "Sriracha")
Coral = Tone(0xFF, 0x57, 0x7D, "Coral")
Salmon = Tone(0xFF, 0x7F, 0x90, "Salmon")
Chili = Tone(0xE2, 0x30, 0x80, "Chili")
Cherry = Tone(0xFF, 0x38, 0x8B, "Cherry")
Tuna = Tone(0xFF, 0x6D, 0xAA, "Tuna")
Macaron = Tone(0xE9, 0x40, 0xB0, "Macaron")
Pony = Tone(0xFF, 0x4F, 0xBF, "Pony")
Cheeky = Tone(0xFF, 0x79, 0xD0, "Cheeky")
Flamingo = Tone(0xF9, 0x47, 0xE3, "Flamingo")
Dolly = Tone(0xFF, 0x60, 0xFF, "Dolly")
Blush = Tone(0xFF, 0x84, 0xFF, "Blush")
Urchin = Tone(0xC3, 0x37, 0xE0, "Urchin")
Mochi = Tone(0xEB, 0x5D, 0xFF, "Mochi")
Lilac = Tone(0xF3, 0x79, 0xFF, "Lilac")
Prince = Tone(0x9C, 0x35, 0xE1, "Prince")
Violet = Tone(0xC2, 0x59, 0xFF, "Violet")
Mauve = Tone(0xD4, 0x6E, 0xFF, "Mauve")
Grape = Tone(0x71, 0x34, 0xDD, "Grape")
Plum = Tone(0x99, 0x53, 0xFF, "Plum")
Orchid = Tone(0xAD, 0x6E, 0xFF, "Orchid")
Jelly = Tone(0x4A, 0x30, 0xD9, "Jelly")
Charple = Tone(0x6B, 0x50, 0xFF, "Charple")
Hazy = Tone(0x8B, 0x75, 0xFF, "Hazy")
Ox = Tone(0x33, 0x31, 0xB2, "Ox")
Sapphire = Tone(0x49, 0x49, 0xFF, "Sapphire")
Guppy = Tone(0x72, 0x72, 0xFF, "Guppy")
Oceania = Tone(0x2B, 0x55, 0xB3, "Oceania")
Thunder = Tone(0x47, 0x76, 0xFF, "Thunder")
Anchovy = Tone(0x71, 0x9A, 0xFC, "Anchovy")
Damson = Tone(0x00, 0x7A, 0xB8, "Damson")
Malibu = Tone(0x00, 0xA4, 0xFF, "Malibu")
Sardine = Tone(0x4F, 0xBE, 0xFE, "Sardine")
Zinc = Tone(0x10, 0xB1, 0xAE, "Zinc")
Turtle = Tone(0x0A, 0xDC, 0xD9, "Turtle")
Lichen = Tone(0x5C, 0xDF, 0xEA, "Lichen")
Guac = Tone(0x12, 0xC7, 0x8F, "Guac")
Julep = Tone(0x00, 0xFF, 0xB2, "Julep")
Bok = Tone(0x68, 0xFF, 0xD6, "Bok")
Mustard = Tone(0xF5, 0xEF, 0x34, "Mustard")
Citron = Tone(0xE8, 0xFF, 0x27, "Citron")
Zest = Tone(0xE8, 0xFE, 0x96, "Zest")
Butter = Tone(0xFF, 0xFA, 0xF1, "Butter")
Pepper = Tone(0x20, 0x1F, 0x26, "Pepper")
BBQ = Tone(0x2D, 0x2C, 0x36, "BBQ")
Char = Tone(0x3A, 0x39, 0x43, "Char")
Iron = Tone(0x4D, 0x4C, 0x57, "Iron")
Oyster = Tone(0x60, 0x5F, 0x6B, "Oyster")
Squid = Tone(0x85, 0x83, 0x92, "Squid")
Steam = Tone(0xA2, 0xA0, 0xAD, "Steam")
Smoke = Tone(0xBF, 0xBC, 0xC8, "Smoke")
Steep = Tone(0xD6, 0xD3, 0xDC, "Steep")
Sash = Tone(0xEC, 0xEB, 0xF0, "Sash")
Salt = Tone(0xF7, 0xF6, 0xFB, "Salt")
Soda = Tone(0xFB, 0xFB, 0xFB, "Soda")
Darple = Tone(0x5B, 0x40, 0xEC, "Darple")
Larple = Tone(0x7B, 0x62, 0xFF, "Larple")
Pickle = Tone(0x00, 0xA4, 0x75, "Pickle")
Gator = Tone(0x18, 0x46, 0x3D, "Gator")
Spinach = Tone(0x1C, 0x36, 0x34, "Spinach")
Pom = Tone(0xAB, 0x24, 0x54, "Pom")
Steak = Tone(0x58, 0x22, 0x38, "Steak")
Toast = Tone(0x41, 0x21, 0x30, "Toast")
Ice = Tone(0x00, 0xFF, 0xFC, "Ice")
# fmt: on

#: Every tone, in Charm's order: the spectrum Cumin to Zest, then Butter,
#: the neutrals, the extra Charples, the diff colours and Ice.
KEYS: tuple[Tone, ...] = (
    Cumin,
    Tang,
    Yam,
    Paprika,
    Bengal,
    Uni,
    Sriracha,
    Coral,
    Salmon,
    Chili,
    Cherry,
    Tuna,
    Macaron,
    Pony,
    Cheeky,
    Flamingo,
    Dolly,
    Blush,
    Urchin,
    Mochi,
    Lilac,
    Prince,
    Violet,
    Mauve,
    Grape,
    Plum,
    Orchid,
    Jelly,
    Charple,
    Hazy,
    Ox,
    Sapphire,
    Guppy,
    Oceania,
    Thunder,
    Anchovy,
    Damson,
    Malibu,
    Sardine,
    Zinc,
    Turtle,
    Lichen,
    Guac,
    Julep,
    Bok,
    Mustard,
    Citron,
    Zest,
    Butter,
    Pepper,
    BBQ,
    Char,
    Iron,
    Oyster,
    Squid,
    Steam,
    Smoke,
    Steep,
    Sash,
    Salt,
    Soda,
    Darple,
    Larple,
    Pickle,
    Gator,
    Spinach,
    Pom,
    Steak,
    Toast,
    Ice,
)

#: The main palette, Cumin through Zest.
SPECTRUM: tuple[Tone, ...] = KEYS[: KEYS.index(Zest) + 1]
#: Pepper through Soda, darkest first.
NEUTRALS: tuple[Tone, ...] = (
    Pepper,
    BBQ,
    Char,
    Iron,
    Oyster,
    Squid,
    Steam,
    Smoke,
    Steep,
    Sash,
    Salt,
    Soda,
)
#: The Charple ramp, darkest first.
CHARPLES: tuple[Tone, ...] = (Jelly, Darple, Charple, Larple, Hazy)
#: Diff additions, darkest first.
ADDITIONS: tuple[Tone, ...] = (Spinach, Gator, Pickle, Julep)
#: Diff deletions, darkest first.
DELETIONS: tuple[Tone, ...] = (Toast, Steak, Pom, Cherry)
#: The core palette.
PRIMARY: tuple[Tone, ...] = (Charple, Dolly, Julep, Zest, Hazy, Blush, Bok, Butter)
#: The secondary palette.
SECONDARY: tuple[Tone, ...] = (Uni, Coral, Tuna, Violet, Malibu, Turtle, Ice)

_BY_NAME = {t.name.lower(): t for t in KEYS}
_BY_HEX = {t.hex: t for t in KEYS}


def by_name(name: str) -> Tone:
    """The tone called *name*, in any case. Raises :class:`KeyError` if none is."""
    return _BY_NAME[name.lower()]


def name_from_hex(hex_value: str) -> str:
    """The tone's name for ``"#6B50FF"``-style *hex_value*, or ``""``."""
    tone = _BY_HEX.get(Color.parse(hex_value).hex)
    return tone.name if tone else ""
