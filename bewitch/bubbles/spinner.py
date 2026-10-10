"""Spinners: Bubbles' frame sets, as data.

The same twelve spinners with the same frames and rates as
``charm.land/bubbles/v2/spinner``. There is no ticking here — a spinner is a
list of frames and a rate, and the app that owns the event loop decides
when to draw the next one. That is deliberate: a library that ran its own
timer would spend wakeups on a screen nobody had asked to animate.

``Globe``, ``Moon`` and ``Monkey`` are emoji, two columns wide and drawn in
their own colours; they are kept because Bubbles has them, not because they
suit a phone terminal.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Spinner:
    frames: tuple[str, ...]
    #: Frames per second.
    fps: float

    @property
    def interval(self) -> float:
        """Seconds between frames."""
        return 1.0 / self.fps

    def frame(self, tick: int) -> str:
        """The frame to show on the *tick*-th step."""
        return self.frames[tick % len(self.frames)]


Line = Spinner(("|", "/", "-", "\\"), 10)
Dot = Spinner(("⣾ ", "⣽ ", "⣻ ", "⢿ ", "⡿ ", "⣟ ", "⣯ ", "⣷ "), 10)
MiniDot = Spinner(("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"), 12)
Jump = Spinner(("⢄", "⢂", "⢁", "⡁", "⡈", "⡐", "⡠"), 10)
Pulse = Spinner(("█", "▓", "▒", "░"), 8)
Points = Spinner(("∙∙∙", "●∙∙", "∙●∙", "∙∙●"), 7)
Globe = Spinner(("🌍", "🌎", "🌏"), 4)
Moon = Spinner(("🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"), 8)
Monkey = Spinner(("🙈", "🙉", "🙊"), 3)
Meter = Spinner(("▱▱▱", "▰▱▱", "▰▰▱", "▰▰▰", "▰▰▱", "▰▱▱", "▱▱▱"), 7)
Hamburger = Spinner(("☱", "☲", "☴", "☲"), 3)
Ellipsis = Spinner(("", ".", "..", "..."), 3)
