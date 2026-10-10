"""The keyboard and the screen, from the standard library: modes and keys.

What a full-screen app needs from its terminal beyond drawing: a keyboard
that delivers keys as they are pressed (cbreak), the alternate screen, a
hidden cursor, application keypad mode, wheel reporting — and a decoder that
turns the bytes the terminal sends back into keys and wheel steps.

This exists instead of blessed, which was the first choice. Measured
2026-10-10 under a pty: on a terminal that answers a cursor-position request
blessed 1.50 starts quickly (about 0.1 s to import, 0.01 s to construct), but
on one that answers nothing it waits out its query timeout — five seconds by
default — while constructing. The deciding problem was the wheel: blessed
decodes SGR mouse reports only once its mouse mode is on, and it switches that
on only if the terminal answers a DECRQM mode query. Where the terminal does
not answer, a wheel report arrives as separate keystrokes — ``<``, ``6``,
``4``, ``;`` — any of which could press a key on a screen where keys spend
data.

So the decoder here holds one rule above the rest: **a byte that began an
escape sequence is never delivered as a key.** A mouse report, a key the
decoder does not know, or a sequence cut off mid-way is dropped whole. And
nothing is asked of the terminal: no queries, so nothing to wait for.
"""

from __future__ import annotations

import codecs
import contextlib
import os
import select
import sys
import termios
import tty
from collections.abc import Iterator
from dataclasses import dataclass
from typing import IO

#: How long a lone ESC waits to see if it starts a sequence — the same
#: 25 ms curses waits (ESCDELAY) on a terminal that is not over a network.
ESC_DELAY = 0.025


@dataclass(frozen=True, slots=True)
class Key:
    """A key: a character (``"a"``, ``"日"``) or a name (``"up"``, ``"enter"``)."""

    name: str

    @property
    def is_char(self) -> bool:
        return len(self.name) == 1 and self.name.isprintable()


@dataclass(frozen=True, slots=True)
class Mouse:
    """A mouse report. ``button`` is ``"wheel_up"``, ``"wheel_down"``,
    ``"left"``, ``"middle"``, ``"right"`` or ``"other"``; ``x``/``y`` are
    0-based cells."""

    button: str
    x: int
    y: int
    released: bool = False
    motion: bool = False

    @property
    def is_wheel(self) -> bool:
        return self.button in ("wheel_up", "wheel_down")


Event = Key | Mouse

_CSI_FINAL = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "H": "home",
    "F": "end",
    "Z": "backtab",
    "E": "begin",
}
_CSI_TILDE = {
    "1": "home",
    "7": "home",
    "4": "end",
    "8": "end",
    "2": "insert",
    "3": "delete",
    "5": "page_up",
    "6": "page_down",
    "11": "f1",
    "12": "f2",
    "13": "f3",
    "14": "f4",
    "15": "f5",
    "17": "f6",
    "18": "f7",
    "19": "f8",
    "20": "f9",
    "21": "f10",
    "23": "f11",
    "24": "f12",
}
_SS3 = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "H": "home",
    "F": "end",
    "P": "f1",
    "Q": "f2",
    "R": "f3",
    "S": "f4",
    "M": "enter",
}
_CONTROL = {
    "\r": "enter",
    "\n": "enter",
    "\x7f": "backspace",
    "\x08": "backspace",
    "\t": "tab",
}
_BUTTONS = {0: "left", 1: "middle", 2: "right", 64: "wheel_up", 65: "wheel_down"}


class Decoder:
    """Bytes in, events out, however the bytes are split between reads.

    :meth:`feed` returns every event the bytes so far complete and holds back
    a sequence that is still arriving; :meth:`flush` is called when the line
    has gone quiet, and resolves what is held — a lone ESC is the escape key,
    and a sequence cut off mid-way is dropped, never spelled out as keys.
    """

    def __init__(self) -> None:
        self._utf8 = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._pending = ""

    def feed(self, data: bytes | str) -> list[Event]:
        text = data if isinstance(data, str) else self._utf8.decode(data)
        self._pending += text
        events, self._pending = _parse(self._pending, final=False)
        return events

    def flush(self) -> list[Event]:
        events, self._pending = _parse(self._pending, final=True)
        return events

    @property
    def waiting(self) -> bool:
        """True while a sequence has started and not yet finished."""
        return bool(self._pending)


def _parse(text: str, final: bool) -> tuple[list[Event], str]:
    events: list[Event] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\x1b":
            events.append(Key(_CONTROL.get(ch, ch)))
            i += 1
            continue
        consumed, event = _escape(text, i)
        if consumed == 0:  # incomplete
            if not final:
                return events, text[i:]
            if i + 1 == len(text):
                events.append(Key("escape"))
            # A sequence cut off mid-way is dropped whole.
            return events, ""
        if event is not None:
            events.append(event)
        i += consumed
    return events, ""


def _escape(text: str, i: int) -> tuple[int, Event | None]:
    """How many characters the escape at *i* takes, and what it means.

    ``(0, None)`` means "not finished yet"; ``(n, None)`` means "a sequence
    this decoder does not know, n characters long: drop it".
    """
    rest = text[i + 1 :]
    if not rest:
        return 0, None
    lead = rest[0]
    if lead == "[":
        return _csi(text, i)
    if lead == "O":
        if len(rest) < 2:
            return 0, None
        name = _SS3.get(rest[1])
        return 3, Key(name) if name else None
    if lead == "\x1b":
        # ESC ESC: the first is the escape key; the second starts again.
        return 1, Key("escape")
    # ESC + a character is Alt+character, which curses delivers as the escape
    # key followed by the character — and so does this.
    return 1, Key("escape")


def _csi(text: str, i: int) -> tuple[int, Event | None]:
    j = i + 2
    if j < len(text) and text[j] == "M":  # legacy mouse: ESC [ M b x y
        if len(text) < j + 4:
            return 0, None
        b, x, y = (ord(c) - 32 for c in text[j + 1 : j + 4])
        return j + 4 - i, _mouse(b, x - 1, y - 1, released=(b & 3) == 3 and b < 64)
    start = j
    while j < len(text) and "\x30" <= text[j] <= "\x3f":
        j += 1
    while j < len(text) and "\x20" <= text[j] <= "\x2f":
        j += 1
    if j >= len(text):
        return 0, None
    final = text[j]
    params = text[start:j]
    length = j + 1 - i
    if not "\x40" <= final <= "\x7e":
        return length, None
    if params.startswith("<") and final in "Mm":  # SGR mouse
        try:
            b, x, y = (int(p) for p in params[1:].split(";"))
        except ValueError:
            return length, None
        return length, _mouse(b, x - 1, y - 1, released=final == "m")
    if final == "~":
        name = _CSI_TILDE.get(params.split(";")[0])
        return length, Key(name) if name else None
    # Modifiers (ESC [ 1 ; 5 A is Ctrl+Up) arrive as numeric parameters; the
    # key is the key either way, which is what curses delivers too.
    name = _CSI_FINAL.get(final)
    if name and all(c.isdigit() or c == ";" for c in params):
        return length, Key(name)
    return length, None


def _mouse(b: int, x: int, y: int, released: bool) -> Mouse:
    motion = bool(b & 32)
    base = b & ~(4 | 8 | 16 | 32)
    return Mouse(_BUTTONS.get(base, "other"), x, y, released=released, motion=motion)


class Terminal:
    """The controlling terminal: its size, its modes, and its keys.

    Modes are context managers that undo themselves on the way out, however
    the way out is taken, so an exception never leaves the phone's terminal
    in cbreak mode on the alternate screen.
    """

    def __init__(self, stream: IO[str] | None = None, fd: int | None = None):
        self.stream = stream or sys.stdout
        self.fd = sys.stdin.fileno() if fd is None else fd
        self.decoder = Decoder()
        self._queue: list[Event] = []

    def write(self, text: str) -> None:
        self.stream.write(text)
        self.stream.flush()

    def size(self) -> tuple[int, int]:
        """``(height, width)`` in cells."""
        try:
            cols, rows = os.get_terminal_size(self.stream.fileno())
        except (OSError, ValueError, AttributeError):
            cols, rows = 80, 24
        return rows, cols

    @contextlib.contextmanager
    def cbreak(self) -> Iterator[None]:
        """Keys as they are pressed, unechoed. Ctrl-C and Ctrl-Z still work."""
        saved = termios.tcgetattr(self.fd)
        try:
            tty.setcbreak(self.fd, termios.TCSANOW)
            yield
        finally:
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, saved)

    @contextlib.contextmanager
    def mode(self, on: str, off: str) -> Iterator[None]:
        self.write(on)
        try:
            yield
        finally:
            self.write(off)

    def fullscreen(self):
        return self.mode("\x1b[?1049h", "\x1b[?1049l")

    def hidden_cursor(self):
        return self.mode("\x1b[?25l", "\x1b[?25h")

    def keypad(self):
        """Application cursor keys, as curses' ``keypad(True)`` asks for."""
        return self.mode("\x1b[?1h\x1b=", "\x1b[?1l\x1b>")

    def mouse(self):
        """Button and wheel reports, in SGR form. Taps are reported too; it
        is the caller's job — and :mod:`bewitch.cursed`'s — to drop them."""
        return self.mode("\x1b[?1000h\x1b[?1006h", "\x1b[?1006l\x1b[?1000l")

    def read(self, timeout: float | None = None) -> Event | None:
        """The next key or mouse report, or ``None`` after *timeout* seconds.

        ``None`` timeout blocks until something arrives. A lone ESC is held
        :data:`ESC_DELAY` to see whether a sequence follows.
        """
        while not self._queue:
            if not self._ready(timeout):
                if self.decoder.waiting:
                    self._queue.extend(self.decoder.flush())
                    continue
                return None
            data = os.read(self.fd, 1024)
            if not data:
                return None
            self._queue.extend(self.decoder.feed(data))
            while self.decoder.waiting and self._ready(ESC_DELAY):
                self._queue.extend(self.decoder.feed(os.read(self.fd, 1024)))
            if self.decoder.waiting:
                self._queue.extend(self.decoder.flush())
        return self._queue.pop(0)

    def _ready(self, timeout: float | None) -> bool:
        readable, _, _ = select.select([self.fd], [], [], timeout)
        return bool(readable)
