"""Semantic colour roles: what a colour is *for*, not what it is.

Recipes and apps name roles (``theme.primary``, ``theme.fg_muted``), never
tones, so a screen can be re-coloured by swapping one :class:`Theme`. The
default, :data:`CHARM`, is the role-to-tone mapping Crush's dark theme
uses — the look the whole package exists to reproduce. The mapping is taken
from how Crush looks, not from its code: which charmtone each role is drawn
in is a design decision, and the code that applies it here is this
package's own.

Crush names its greys by how far they recede (``fgSubtle``,
``fgMoreSubtle``, ``fgMostSubtle``); those are kept, with the plainer
``fg_muted`` as an alias for the middle one, because "muted" is the word
everyone reaches for first.
"""

from __future__ import annotations

from dataclasses import dataclass

from bewitch import charmtone as ct
from bewitch.color import Color


@dataclass(frozen=True, slots=True)
class Theme:
    #: The brand colour: selection bars, dialog borders, the header band.
    primary: Color
    #: Its partner: gradient ends, scrollbar thumbs, the Charm™ mark.
    secondary: Color
    #: A bright highlight, used sparingly.
    accent: Color

    #: Body text.
    fg_base: Color
    #: Section titles; one step back from body text.
    fg_subtle: Color
    #: Secondary lines, keys in a help line.
    fg_more_subtle: Color
    #: Tertiary lines, descriptions in a help line.
    fg_most_subtle: Color
    #: Text on a primary-coloured background.
    on_primary: Color

    #: The app's own background, where it paints one.
    bg_base: Color
    #: A panel barely lifted off the background.
    bg_least_visible: Color
    #: A panel lifted a little more.
    bg_less_visible: Color
    #: The most lifted surface: disabled selections, inactive buttons.
    bg_most_visible: Color

    #: Rules, help separators, scrollbar tracks: there, but quiet.
    separator: Color

    #: Things that delete or cancel.
    destructive: Color
    error: Color
    warning: Color
    warning_subtle: Color
    #: Something that wants attention now.
    attention: Color
    #: Working: spinners, "in progress".
    busy: Color
    info: Color
    info_more_subtle: Color
    info_most_subtle: Color
    success: Color
    success_more_subtle: Color
    success_most_subtle: Color

    @property
    def fg_muted(self) -> Color:
        return self.fg_more_subtle


#: Crush's dark theme.
CHARM = Theme(
    primary=ct.Charple,
    secondary=ct.Dolly,
    accent=ct.Bok,
    fg_base=ct.Sash,
    fg_subtle=ct.Smoke,
    fg_more_subtle=ct.Squid,
    fg_most_subtle=ct.Oyster,
    on_primary=ct.Butter,
    bg_base=ct.Pepper,
    bg_least_visible=ct.BBQ,
    bg_less_visible=ct.Char,
    bg_most_visible=ct.Iron,
    separator=ct.Char,
    destructive=ct.Coral,
    error=ct.Sriracha,
    warning=ct.Mustard,
    warning_subtle=ct.Zest,
    attention=ct.Tang,
    busy=ct.Citron,
    info=ct.Malibu,
    info_more_subtle=ct.Sardine,
    info_most_subtle=ct.Damson,
    success=ct.Julep,
    success_more_subtle=ct.Bok,
    success_most_subtle=ct.Guac,
)
