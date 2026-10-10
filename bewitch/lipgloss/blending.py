"""Gradients: Lip Gloss's ``Blend1D``, and the text gradient Crush draws.

:func:`blend_1d` is a line-for-line port: the same segment arithmetic (the
first segments take the remainder), the same CIELAB blend, the same answers.
:func:`foreground_gradient` is the piece Crush builds on top of it for its
logo and dialog titles — one colour per character, the stops spread across
the whole string.
"""

from __future__ import annotations

from bewitch.color import Color, ColorLike, to_color
from bewitch.lipgloss._cells import EMPTY, Pen, Span, char_width


def blend_1d(steps: int, *stops: ColorLike | None) -> list[Color]:
    """*steps* colours running through *stops* in order, blended in Lab.

    With no more steps than stops it returns the first *steps* stops, and
    with a single stop it returns that stop *steps* times — both exactly as
    Lip Gloss does. ``None`` stops are dropped.
    """
    steps = max(0, steps)
    colors = [c for c in (to_color(s) for s in stops) if c is not None]
    if steps <= len(colors):
        return colors[:steps]
    if not colors:
        return []
    if len(colors) == 1:
        return [colors[0]] * steps

    segments = len(colors) - 1
    size, extra = divmod(steps, segments)
    out: list[Color] = []
    for i in range(segments):
        start, end = colors[i], colors[i + 1]
        n = size + (1 if i < extra else 0)
        for j in range(n):
            out.append(start.blend(end, j / (n - 1) if n > 1 else 0.0))
    return out


def foreground_gradient(text: str, *stops: ColorLike, pen: Pen = EMPTY) -> list[Span]:
    """*text* with its foreground running through *stops*, one per character.

    Zero-width marks take the colour of the character they sit on, so an
    accent never gets a colour of its own. *pen* carries anything else the
    text should have (bold, a background) and its own ``fg`` is ignored.
    """
    clusters: list[str] = []
    for ch in text:
        if clusters and char_width(ch) == 0:
            clusters[-1] += ch
        else:
            clusters.append(ch)
    ramp = blend_1d(len(clusters), *stops)
    return [
        Span(cluster, Pen(color, *_rest(pen)))
        for cluster, color in zip(clusters, ramp, strict=True)
    ]


def _rest(pen: Pen) -> tuple:
    return (
        pen.bg,
        pen.bold,
        pen.faint,
        pen.italic,
        pen.underline,
        pen.strikethrough,
        pen.reverse,
    )
