"""Colours: parsing, CIELAB, blending and distance.

A :class:`Color` is three 8-bit channels and nothing else. Alpha is left out
on purpose: a terminal cell has no transparency, and Lip Gloss itself treats
a fully transparent stop as an opaque one ("the alpha was lost in
conversion") rather than blending with nothing.

Blending and distance work in CIELAB (D65), which is what Lip Gloss v2's
``Blend1D`` uses through go-colorful's ``BlendLab``. A gradient made in RGB
sags through a muddy grey in the middle; one made in Lab does not, and that
middle is most of what a two-stop title gradient shows.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_HEX = re.compile(r"#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})")

# D65 reference white, the one go-colorful's Lab() uses.
_XN, _YN, _ZN = 0.95047, 1.00000, 1.08883


@dataclass(frozen=True, slots=True, eq=False)
class Color:
    """An sRGB colour, one byte per channel.

    Two colours are equal when their channels are, whatever their class: a
    :class:`~bewitch.charmtone.Tone` and the same hex parsed by hand are the
    same colour, and a test asserting otherwise is asserting about a name.
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel in (self.r, self.g, self.b):
            if not 0 <= channel <= 255:
                raise ValueError(f"channel out of range 0-255: {channel}")

    @classmethod
    def parse(cls, value: str | Color) -> Color:
        """A colour from ``"#6B50FF"``, ``"6b50ff"``, ``"#fff"`` or a Color."""
        if isinstance(value, Color):
            return value
        found = _HEX.fullmatch(value.strip())
        if not found:
            raise ValueError(f"not a hex colour: {value!r}")
        digits = found.group(1)
        if len(digits) == 3:
            digits = "".join(d * 2 for d in digits)
        return cls(int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))

    @property
    def hex(self) -> str:
        """``"#RRGGBB"``, uppercase, as charmtone spells its values."""
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return self.rgb == other.rgb

    def __hash__(self) -> int:
        return hash(self.rgb)

    def __repr__(self) -> str:
        return f"Color({self.hex!r})"

    def lab(self) -> tuple[float, float, float]:
        """CIE L*a*b* under D65."""
        x, y, z = _xyz(self.r, self.g, self.b)
        fx, fy, fz = _lab_f(x / _XN), _lab_f(y / _YN), _lab_f(z / _ZN)
        return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))

    @classmethod
    def from_lab(cls, lightness: float, a: float, b: float) -> Color:
        """The nearest sRGB colour to a Lab one, clamped into gamut."""
        fy = (lightness + 16.0) / 116.0
        fx = fy + a / 500.0
        fz = fy - b / 200.0
        x, y, z = _XN * _lab_finv(fx), _YN * _lab_finv(fy), _ZN * _lab_finv(fz)
        return cls(*(_to_byte(_compand(c)) for c in _xyz_to_linear(x, y, z)))

    def blend(self, other: Color, t: float) -> Color:
        """The colour *t* of the way from this one to *other*, through Lab.

        ``t`` is clamped to 0-1, so the ends are exactly the two colours.
        """
        if t <= 0:
            return self
        if t >= 1:
            return other
        a, b = self.lab(), other.lab()
        return Color.from_lab(*(p + (q - p) * t for p, q in zip(a, b, strict=True)))

    def distance(self, other: Color) -> float:
        """Perceptual distance: CIE76 ΔE, the Euclidean distance in Lab."""
        return math.dist(self.lab(), other.lab())


ColorLike = Color | str


def to_color(value: ColorLike | None) -> Color | None:
    """A :class:`Color` from a Color, a hex string or ``None``."""
    if value is None:
        return None
    return Color.parse(value)


def _linearize(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _compand(c: float) -> float:
    c = min(1.0, max(0.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _to_byte(c: float) -> int:
    # go-colorful's RGB255: round half up, after clamping.
    return int(min(1.0, max(0.0, c)) * 255.0 + 0.5)


def _xyz(r: int, g: int, b: int) -> tuple[float, float, float]:
    lr, lg, lb = _linearize(r), _linearize(g), _linearize(b)
    return (
        0.4124564 * lr + 0.3575761 * lg + 0.1804375 * lb,
        0.2126729 * lr + 0.7151522 * lg + 0.0721750 * lb,
        0.0193339 * lr + 0.1191920 * lg + 0.9503041 * lb,
    )


def _xyz_to_linear(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (
        3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
        -0.9692660 * x + 1.8760108 * y + 0.0415560 * z,
        0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
    )


_EPSILON = 216 / 24389
_KAPPA = 24389 / 27


def _lab_f(t: float) -> float:
    return t ** (1 / 3) if t > _EPSILON else (_KAPPA * t + 16) / 116


def _lab_finv(t: float) -> float:
    cubed = t**3
    return cubed if cubed > _EPSILON else (116 * t - 16) / _KAPPA
