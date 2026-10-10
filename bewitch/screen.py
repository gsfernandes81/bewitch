"""``Frame``: a whole screen written to the terminal, changed lines only.

The full-screen half of the ANSI adapter. An app builds each screen as one
:class:`~bewitch.lipgloss.Block` the size of the terminal (a
:class:`~bewitch.lipgloss.Canvas` makes that easy) and hands it to
:meth:`Frame.show`. The frame remembers what it last wrote and writes only
the lines that differ, each positioned with a cursor move.

**An unchanged screen writes nothing at all** — not a cursor move, not a
synchronisation marker — so an app that redraws on every wakeup still costs
the terminal nothing while it sits idle. ytq holds that as a property with a
test, and this is what lets it keep holding it after leaving curses.

It writes through whatever function it is given, so it works with blessed
(``Frame(term.stream.write)``), with a raw ``sys.stdout.write``, or with a
test's list. It does not enter the alternate screen, hide the cursor or read
keys: those belong to the TUI library that owns the terminal.
"""

from __future__ import annotations

from collections.abc import Callable

from bewitch import ansi
from bewitch.colorprofile import Profile, detect
from bewitch.lipgloss._cells import Block

#: Synchronised output (DEC mode 2026): the terminal holds the frame and
#: shows it whole, so a redraw never tears. A terminal that does not know
#: the mode ignores it.
SYNC_BEGIN = "\x1b[?2026h"
SYNC_END = "\x1b[?2026l"
CLEAR = "\x1b[2J"


def _move(row: int, col: int = 0) -> str:
    return f"\x1b[{row + 1};{col + 1}H"


class Frame:
    def __init__(
        self,
        write: Callable[[str], object],
        profile: Profile | None = None,
        flush: Callable[[], object] | None = None,
        synchronized: bool = True,
    ):
        self._write = write
        self._flush = flush
        self.profile = detect() if profile is None else profile
        self.synchronized = synchronized
        self._last: list[str] | None = None
        self._width = -1

    def invalidate(self) -> None:
        """Forget what is on screen: the next :meth:`show` redraws it all.

        Call it after a resize, or after anything else has written to the
        terminal (a shell-out, a suspend).
        """
        self._last = None

    def show(self, block: Block) -> int:
        """Bring the terminal to *block*; return the characters written."""
        lines = [ansi.line(spans, self.profile) for spans in block.lines]
        redraw = self._last is None or block.width != self._width
        parts: list[str] = []
        if redraw:
            parts.append(CLEAR)
            changed = range(len(lines))
        else:
            previous = self._last
            changed = [
                i
                for i, line in enumerate(lines)
                if i >= len(previous) or previous[i] != line
            ]
            # Rows the new screen no longer has are blanked, not left behind.
            for i in range(len(lines), len(previous)):
                parts.append(_move(i) + "\x1b[2K")
        for i in changed:
            parts.append(_move(i) + lines[i])
        self._last = lines
        self._width = block.width
        if not parts:
            return 0
        out = "".join(parts)
        if self.synchronized:
            out = SYNC_BEGIN + out + SYNC_END
        self._write(out)
        if self._flush:
            self._flush()
        return len(out)
