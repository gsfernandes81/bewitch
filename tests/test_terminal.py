"""The keyboard decoder, and ``cursed`` — the curses-shaped facade — on a pty.

The decoder's one rule is checked as a property: however the bytes of a
mouse report or an unknown sequence are split between reads, none of them is
ever delivered as a key. Then ``cursed`` is run for real, under a
pseudo-terminal, and read back through ``pyte`` — the same way ytq's and
dlq's screen tests read their screens — so what is checked is what a
terminal would show and what the app would be told.
"""

from __future__ import annotations

import os
import pty
import select
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pyte
import pytest
from hypothesis import given
from hypothesis import strategies as st

from bewitch import cursed
from bewitch.terminal import Decoder, Key, Mouse

ROOT = Path(__file__).resolve().parent.parent

# Decoder -------------------------------------------------------------------

SEQUENCES = {
    "\x1b[A": Key("up"),
    "\x1bOB": Key("down"),
    "\x1b[1;5C": Key("right"),
    "\x1b[5~": Key("page_up"),
    "\x1b[H": Key("home"),
    "\x1b[4~": Key("end"),
    "\r": Key("enter"),
    "\x7f": Key("backspace"),
    "q": Key("q"),
    "日": Key("日"),
    "\x1b[<64;3;4M": Mouse("wheel_up", 2, 3),
    "\x1b[<65;1;1M": Mouse("wheel_down", 0, 0),
    "\x1b[<0;5;6M": Mouse("left", 4, 5),
    "\x1b[<0;5;6m": Mouse("left", 4, 5, released=True),
}
#: Sequences the decoder does not know. They must vanish, byte and all.
UNKNOWN = ["\x1b[200~", "\x1b[?62;c", "\x1b[38;5;1m", "\x1bOx", "\x1b[99X"]


def _decode(chunks: list[bytes]) -> list:
    decoder = Decoder()
    events = []
    for chunk in chunks:
        events += decoder.feed(chunk)
    return events + decoder.flush()


def _split(data: bytes, cuts: list[int]) -> list[bytes]:
    points = sorted({c % (len(data) + 1) for c in cuts})
    pieces, last = [], 0
    for p in points:
        pieces.append(data[last:p])
        last = p
    return [*pieces, data[last:]]


@given(
    st.lists(st.sampled_from(sorted(SEQUENCES) + UNKNOWN), max_size=12),
    st.lists(st.integers(0, 200), max_size=8),
)
def test_however_the_bytes_are_split_the_same_keys_arrive(seq, cuts):
    data = "".join(seq).encode()
    expected = [SEQUENCES[s] for s in seq if s in SEQUENCES]
    assert _decode(_split(data, cuts)) == expected


@given(st.integers(0, 127), st.integers(1, 300), st.integers(1, 300), st.data())
def test_no_byte_of_a_mouse_report_is_ever_a_key(button, x, y, data):
    report = f"\x1b[<{button};{x};{y}M".encode()
    cuts = data.draw(st.lists(st.integers(0, len(report)), max_size=6))
    events = _decode(_split(report, cuts))
    assert all(isinstance(e, Mouse) for e in events)


@given(st.integers(1, 11))
def test_a_sequence_cut_off_mid_way_is_dropped_whole(n):
    report = b"\x1b[<64;30;40M"[:n]  # twelve bytes whole; every shorter cut
    events = _decode([report])
    assert events in ([], [Key("escape")])
    if n > 1:
        assert events == []


def test_a_lone_escape_is_the_escape_key_once_the_line_is_quiet():
    decoder = Decoder()
    assert decoder.feed(b"\x1b") == []
    assert decoder.waiting
    assert decoder.flush() == [Key("escape")]


def test_alt_and_a_letter_is_escape_then_the_letter_as_curses_gives_it():
    assert _decode([b"\x1bx"]) == [Key("escape"), Key("x")]


# The facade, without a terminal -------------------------------------------


def test_attributes_become_pens():
    cursed._state.pairs[3] = (cursed.COLOR_RED, -1)
    pen = cursed._pen(cursed.A_BOLD | cursed.A_DIM | cursed.color_pair(3))
    assert pen.bold and pen.faint
    assert pen.fg.n == cursed.COLOR_RED and pen.bg is None
    assert cursed._pen(cursed.A_REVERSE).reverse


class _FakeTerminal:
    def __init__(self, events):
        self.events = list(events)
        self.written: list[str] = []

    def size(self):
        return (5, 20)

    def read(self, timeout=None):
        return self.events.pop(0) if self.events else None

    def write(self, text):
        self.written.append(text)


def _window(events, mask=0):
    from bewitch.screen import Frame

    terminal = _FakeTerminal(events)
    cursed._state.__init__()
    cursed._state.mouse_mask = mask
    frame = Frame(terminal.write, profile=cursed.Profile.NO_TTY, synchronized=False)
    return cursed.Window(terminal, frame), terminal


def test_keys_arrive_with_curses_codes():
    win, _ = _window([Key("up"), Key("enter"), Key("q"), Key("backspace"), Key("escape")])
    codes = [win.getch() for _ in range(5)]
    assert codes == [cursed.KEY_UP, 10, ord("q"), cursed.KEY_BACKSPACE, 27]
    win.timeout(0)
    assert win.getch() == cursed.ERR


def test_a_tap_never_reaches_an_app_that_asked_for_the_wheel_only():
    mask = cursed.BUTTON4_PRESSED | cursed.BUTTON5_PRESSED
    win, _ = _window([Mouse("left", 1, 1), Mouse("wheel_down", 1, 1), Key("x")], mask)
    assert win.getch() == cursed.KEY_MOUSE
    assert cursed.getmouse()[4] == cursed.BUTTON5_PRESSED
    assert win.getch() == ord("x")


def test_drawing_off_the_edge_is_clipped_not_raised():
    win, terminal = _window([])
    win.erase()
    win.addstr(4, 18, "overflowing")
    win.addstr(9, 0, "below")
    win.addnstr(0, 0, "abcdef", 3, cursed.A_BOLD)
    win.refresh()
    assert "abc" in "".join(terminal.written)
    assert "def" not in "".join(terminal.written)


# The facade, on a real pty -------------------------------------------------

APP = textwrap.dedent(
    """
    import sys
    sys.path.insert(0, {root!r})
    from bewitch import cursed as curses
    from bewitch import bubbles

    def app(win):
        curses.curs_set(0)
        curses.mousemask(curses.BUTTON4_PRESSED | curses.BUTTON5_PRESSED)
        seen = []
        while True:
            win.erase()
            h, w = win.getmaxyx()
            win.draw(0, 0, bubbles.header("demo", ["pty"], w))
            win.addstr(2, 0, "seen: " + ",".join(seen), curses.A_BOLD)
            win.refresh()
            win.timeout(200)
            key = win.getch()
            if key == ord("q"):
                return seen
            if key == -1:
                continue
            seen.append(str(key))

    print("RESULT", curses.wrapper(app))
    """
)


def _run(keys: list[bytes], idle: float = 0.0):
    pid, fd = pty.fork()
    if pid == 0:  # pragma: no cover - the child
        os.environ.update(TERM="xterm-256color", COLUMNS="40", LINES="12")
        os.execv(sys.executable, [sys.executable, "-c", APP.format(root=str(ROOT))])
    subprocess.run(["true"])  # let the child start
    import fcntl
    import struct
    import termios

    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 12, 40, 0, 0))
    screen = pyte.Screen(40, 12)
    stream = pyte.ByteStream(screen)
    out = bytearray()

    def pump(seconds):
        end = time.monotonic() + seconds
        got = 0
        while time.monotonic() < end:
            ready, _, _ = select.select([fd], [], [], 0.05)
            if ready:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    return got
                out.extend(data)
                stream.feed(data)
                got += len(data)
        return got

    pump(1.5)
    idle_bytes = pump(idle) if idle else None
    for key in keys:
        os.write(fd, key)
        pump(0.3)
    pump(1.0)
    os.waitpid(pid, 0)
    return screen, bytes(out), idle_bytes


@pytest.mark.skipif(sys.platform != "linux", reason="needs a Linux pty")
def test_cursed_runs_an_app_on_a_real_terminal():
    screen, out, _ = _run([b"\x1bOA", b"\x1b[<0;3;3M", b"\x1b[<65;3;3M", b"x", b"q"])
    text = "\n".join(screen.display)
    # Up arrives as KEY_UP, the tap never arrives, the wheel arrives as
    # KEY_MOUSE, and x as itself.
    assert f"RESULT ['{cursed.KEY_UP}', '{cursed.KEY_MOUSE}', '120']" in text
    assert b"\x1b[?1049h" in out and b"\x1b[?1049l" in out  # alt screen, and back


@pytest.mark.skipif(sys.platform != "linux", reason="needs a Linux pty")
def test_an_idle_cursed_screen_writes_nothing():
    # The app redraws on every 200 ms timeout; an unchanged frame must cost
    # the terminal nothing — the property ytq's idle-screen test pins.
    _, _, idle_bytes = _run([b"q"], idle=1.2)
    assert idle_bytes == 0
