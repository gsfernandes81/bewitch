"""``cursed``: the slice of ``curses`` an existing app uses, drawn by bewitch.

``from bewitch import cursed as curses`` and an app written for curses keeps
running — the same ``wrapper``, the same window calls, the same key codes —
but its screen is composed on a :class:`~bewitch.lipgloss.Canvas`, written by
a :class:`~bewitch.screen.Frame` (changed lines only, nothing when nothing
changed) and read through :mod:`bewitch.terminal` (no dependencies, no
terminal queries). That makes the move off curses a one-line change that can
be checked on its own, before any screen is restyled; restyling is then
:meth:`Window.draw`, which takes a bewitch :class:`~bewitch.lipgloss.Block`.

It is the slice ytq and dlq use, not all of curses:

* windows: ``getmaxyx``, ``erase``, ``clear``, ``refresh``, ``addstr``,
  ``addnstr``, ``move``, ``getch``, ``timeout``, ``nodelay``, ``keypad``;
* ``wrapper``, ``curs_set``, ``mousemask``, ``getmouse``, the colour-pair
  calls, ``error``, and the ``A_*``, ``COLOR_*``, ``KEY_*`` and
  ``BUTTON*`` constants with curses' own values.

Two behaviours are deliberately curses' and not the terminal's:

* ``getch`` returns ``-1`` on a timeout and ``KEY_RESIZE`` after the window
  changes size, and **mouse reports outside the mask are dropped**: an app
  that asked for wheel events only never sees a tap — the rule ytq is built
  on, that a tap must never press a key.
* Writing to the last cell, or off the edge, is clipped rather than raised.
  Curses raises there and every caller suppresses it; this simply does not.
"""

from __future__ import annotations

import contextlib
import os
import signal
import time
from collections.abc import Callable
from typing import Any, TypeVar

from bewitch.colorprofile import Indexed, Profile, detect
from bewitch.lipgloss import Block, Canvas, Pen
from bewitch.lipgloss._cells import to_row, truncate_row
from bewitch.screen import Frame
from bewitch.terminal import Key, Mouse, Terminal

T = TypeVar("T")


class error(Exception):  # noqa: N801 — curses' own name
    """Raised where curses raises ``curses.error``."""


ERR = -1
OK = 0

# Attributes, with ncurses' bit values.
A_NORMAL = 0
A_STANDOUT = 0x10000
A_UNDERLINE = 0x20000
A_REVERSE = 0x40000
A_BLINK = 0x80000
A_DIM = 0x100000
A_BOLD = 0x200000
A_ITALIC = 0x80000000
A_COLOR = 0xFF00

COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW = 0, 1, 2, 3
COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_WHITE = 4, 5, 6, 7

# Keys, with curses' values.
KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT, KEY_HOME = 258, 259, 260, 261, 262
KEY_BACKSPACE = 263
KEY_F0 = 264
KEY_DC, KEY_IC = 330, 331
KEY_NPAGE, KEY_PPAGE = 338, 339
KEY_ENTER = 343
KEY_BTAB = 353
KEY_END = 360
KEY_MOUSE = 409
KEY_RESIZE = 410

# Mouse buttons, with ncurses' (mouse version 2) values.
BUTTON1_PRESSED = 0x2
BUTTON1_RELEASED = 0x1
BUTTON2_PRESSED = 0x40
BUTTON3_PRESSED = 0x800
BUTTON4_PRESSED = 0x10000
BUTTON5_PRESSED = 0x200000
ALL_MOUSE_EVENTS = 0x3FFFFFF

_KEYS = {
    "up": KEY_UP,
    "down": KEY_DOWN,
    "left": KEY_LEFT,
    "right": KEY_RIGHT,
    "home": KEY_HOME,
    "end": KEY_END,
    "page_up": KEY_PPAGE,
    "page_down": KEY_NPAGE,
    "backspace": KEY_BACKSPACE,
    "delete": KEY_DC,
    "insert": KEY_IC,
    "backtab": KEY_BTAB,
    # curses, with nl() in force, delivers Enter as a newline.
    "enter": 10,
    "tab": 9,
    "escape": 27,
    **{f"f{n}": KEY_F0 + n for n in range(1, 13)},
}
_BUTTON_BITS = {
    "left": BUTTON1_PRESSED,
    "middle": BUTTON2_PRESSED,
    "right": BUTTON3_PRESSED,
    "wheel_up": BUTTON4_PRESSED,
    "wheel_down": BUTTON5_PRESSED,
}


class _State:
    """What curses keeps globally, kept here for the one screen there is."""

    def __init__(self) -> None:
        self.terminal: Terminal | None = None
        self.frame: Frame | None = None
        self.mouse_mask = 0
        self.mouse_mode: contextlib.ExitStack | None = None
        self.last_mouse: tuple[int, int, int, int, int] | None = None
        self.cursor_visible = False
        self.pairs: dict[int, tuple[int, int]] = {}
        self.resized = False
        self.waiting = False
        self.profile = Profile.TRUE_COLOR


_state = _State()


class _Resized(Exception):
    pass


def _pen(attr: int) -> Pen:
    fg = bg = None
    pair = (attr & A_COLOR) >> 8
    if pair and pair in _state.pairs:
        f, b = _state.pairs[pair]
        fg = Indexed(f) if f >= 0 else None
        bg = Indexed(b) if b >= 0 else None
    return Pen(
        fg=fg,
        bg=bg,
        bold=True if attr & A_BOLD else None,
        faint=True if attr & A_DIM else None,
        italic=True if attr & A_ITALIC else None,
        underline=True if attr & A_UNDERLINE else None,
        reverse=True if attr & (A_REVERSE | A_STANDOUT) else None,
    )


class Window:
    """The one full-screen window, as curses' ``stdscr`` behaves."""

    def __init__(self, terminal: Terminal, frame: Frame):
        self._terminal = terminal
        self._frame = frame
        self._timeout: float | None = None
        self._cursor = (0, 0)
        self._shown: tuple[int, int] | None = None
        height, width = terminal.size()
        self._canvas = Canvas(width, height)

    # Size and drawing ----------------------------------------------------

    def getmaxyx(self) -> tuple[int, int]:
        return self._terminal.size()

    def erase(self) -> None:
        height, width = self._terminal.size()
        if (width, height) != (self._canvas.width, self._canvas.height):
            self._canvas.resize(width, height)
        else:
            self._canvas.clear()

    def clear(self) -> None:
        self.erase()
        self._frame.invalidate()

    def addnstr(self, y: int, x: int, text: str, n: int, attr: int = 0) -> None:
        if n <= 0 or y < 0 or x < 0:
            return
        row = truncate_row(to_row(text.replace("\n", " "), _pen(attr)), n)
        self._canvas.compose(Block.from_rows([row]), x, y)

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.addnstr(y, x, text, max(0, self._canvas.width - x), attr)

    def draw(self, y: int, x: int, block: Block) -> None:
        """Compose a bewitch :class:`Block` at row *y*, column *x*."""
        self._canvas.compose(block, x, y)

    def move(self, y: int, x: int) -> None:
        self._cursor = (y, x)

    def refresh(self) -> None:
        wrote = self._frame.show(self._canvas.render())
        if _state.cursor_visible and (wrote or self._cursor != self._shown):
            y, x = self._cursor
            self._terminal.write(f"\x1b[{y + 1};{x + 1}H")
            self._shown = self._cursor

    # Input -----------------------------------------------------------------

    def keypad(self, flag: bool) -> None:
        """Keypad mode is on for the whole of :func:`wrapper`; nothing to do."""

    def timeout(self, ms: int) -> None:
        self._timeout = None if ms < 0 else ms / 1000.0

    def nodelay(self, flag: bool) -> None:
        self._timeout = 0.0 if flag else None

    def getch(self) -> int:
        deadline = None if self._timeout is None else time.monotonic() + self._timeout
        while True:
            if _state.resized:
                _state.resized = False
                self._frame.invalidate()
                return KEY_RESIZE
            remaining = (
                None if deadline is None else max(0.0, deadline - time.monotonic())
            )
            _state.waiting = True
            try:
                event = self._terminal.read(remaining)
            except _Resized:
                continue
            finally:
                _state.waiting = False
            if event is None:
                return ERR
            if isinstance(event, Mouse):
                code = self._mouse(event)
                if code is not None:
                    return code
                if deadline is not None and time.monotonic() >= deadline:
                    return ERR
                continue
            return _code(event)

    def _mouse(self, event: Mouse) -> int | None:
        bit = _BUTTON_BITS.get(event.button, 0)
        if event.released or event.motion or not bit & _state.mouse_mask:
            return None
        _state.last_mouse = (0, event.x, event.y, 0, bit)
        return KEY_MOUSE


def _code(key: Key) -> int:
    if key.name in _KEYS:
        return _KEYS[key.name]
    if len(key.name) == 1:
        return ord(key.name)
    return ERR


# Module functions ----------------------------------------------------------


def wrapper(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run *func(window, …)* full-screen, and put the terminal back after.

    The terminal is restored on every way out — a return, an exception, a
    Ctrl-C — and on a suspend (Ctrl-Z) while it is stopped, as curses does.
    """
    terminal = Terminal()
    profile = detect(terminal.stream)
    frame = Frame(terminal.write, profile=profile)
    _state.__init__()
    _state.terminal, _state.frame, _state.profile = terminal, frame, profile
    window = Window(terminal, frame)
    with contextlib.ExitStack() as stack:
        stack.enter_context(terminal.cbreak())
        stack.enter_context(terminal.fullscreen())
        stack.enter_context(terminal.keypad())
        stack.enter_context(terminal.hidden_cursor())
        stack.callback(_restore_mouse)
        stack.enter_context(_signals(terminal, frame))
        return func(window, *args, **kwargs)


@contextlib.contextmanager
def _signals(terminal: Terminal, frame: Frame):
    def on_resize(signum, _frame):
        _state.resized = True
        if _state.waiting:
            raise _Resized

    def on_suspend(signum, _frame):
        # Leave the terminal as the shell expects it, stop, and on the way
        # back put it all back and redraw from scratch.
        terminal.write("\x1b[?1000l\x1b[?1006l\x1b[?25h\x1b[?1l\x1b>\x1b[?1049l")
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTSTP)
        signal.signal(signal.SIGTSTP, on_suspend)
        terminal.write("\x1b[?1049h\x1b[?1h\x1b=")
        if not _state.cursor_visible:
            terminal.write("\x1b[?25l")
        if _state.mouse_mask:
            terminal.write("\x1b[?1000h\x1b[?1006h")
        frame.invalidate()
        on_resize(signum, _frame)

    previous = {}
    for sig, handler in ((signal.SIGWINCH, on_resize), (signal.SIGTSTP, on_suspend)):
        with contextlib.suppress(ValueError, OSError):  # not the main thread
            previous[sig] = signal.signal(sig, handler)
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _restore_mouse() -> None:
    if _state.mouse_mode is not None:
        _state.mouse_mode.close()
        _state.mouse_mode = None


def curs_set(visibility: int) -> int:
    was = 1 if _state.cursor_visible else 0
    _state.cursor_visible = bool(visibility)
    if _state.terminal:
        _state.terminal.write("\x1b[?25h" if visibility else "\x1b[?25l")
    return was


def mousemask(mask: int) -> tuple[int, int]:
    """Ask for the mouse events in *mask*; the rest are dropped unseen."""
    old = _state.mouse_mask
    _state.mouse_mask = mask
    if mask and _state.mouse_mode is None and _state.terminal:
        _state.mouse_mode = contextlib.ExitStack()
        _state.mouse_mode.enter_context(_state.terminal.mouse())
    elif not mask:
        _restore_mouse()
    return mask, old


def getmouse() -> tuple[int, int, int, int, int]:
    """``(id, x, y, z, bstate)`` of the last mouse event ``getch`` reported."""
    if _state.last_mouse is None:
        raise error("no mouse event")
    return _state.last_mouse


def has_colors() -> bool:
    return _state.profile >= Profile.ANSI


def start_color() -> None:
    pass


def use_default_colors() -> None:
    pass


def init_pair(pair: int, fg: int, bg: int) -> None:
    if not 1 <= pair <= 255:
        raise error(f"color pair out of range: {pair}")
    _state.pairs[pair] = (fg, bg)


def color_pair(pair: int) -> int:
    return (pair << 8) & A_COLOR


def pair_number(attr: int) -> int:
    return (attr & A_COLOR) >> 8


def napms(ms: int) -> int:
    time.sleep(ms / 1000)
    return OK


def beep() -> None:
    pass
