"""Composing a screen, and writing it: the canvas and the frame."""

from __future__ import annotations

from conftest import texts
from hypothesis import given
from hypothesis import strategies as st

from bewitch.colorprofile import Profile
from bewitch.lipgloss import Block, Canvas, Style, string_width
from bewitch.screen import CLEAR, SYNC_BEGIN, SYNC_END, Frame

placements = st.lists(
    st.tuples(texts, st.integers(-10, 50), st.integers(-5, 15)), max_size=6
)


@given(st.integers(0, 50), st.integers(0, 12), placements)
def test_a_canvas_never_grows_whatever_is_composed_onto_it(w, h, placed):
    canvas = Canvas(w, h)
    for text, x, y in placed:
        canvas.compose(Style().render(text), x, y)
    block = canvas.render()
    assert (block.width, block.height) == (w, h)
    for line in block.lines:
        assert string_width("".join(s.text for s in line)) == w


def test_later_blocks_are_drawn_over_earlier_ones():
    canvas = Canvas(5, 1).compose(Block.text("aaaaa")).compose(Block.text("b"), 2)
    assert canvas.render().plain() == "aabaa"


def test_covering_half_a_wide_character_blanks_the_other_half():
    canvas = Canvas(4, 1).compose(Block.text("日本"))
    assert canvas.compose(Block.text("x"), 1).render().plain() == " x本"
    canvas = Canvas(4, 1).compose(Block.text("日本"))
    assert canvas.compose(Block.text("x"), 2).render().plain() == "日x "


def test_a_wide_character_off_the_edge_becomes_a_space():
    assert Canvas(3, 1).compose(Block.text("ab日")).render().plain() == "ab "


def _frame():
    out: list[str] = []
    return Frame(out.append, profile=Profile.TRUE_COLOR, synchronized=False), out


def test_an_unchanged_screen_writes_nothing_at_all():
    frame, out = _frame()
    screen = Style().foreground("#6B50FF").render("one\ntwo")
    assert frame.show(screen) > 0
    written = len(out)
    for _ in range(5):
        assert frame.show(screen) == 0
    assert len(out) == written


def test_only_the_changed_line_is_written():
    frame, out = _frame()
    frame.show(Block.text("one\ntwo\nsix"))
    frame.show(Block.text("one\nTWO\nsix"))
    assert out[-1] == "\x1b[2;1HTWO"


def test_the_first_frame_and_a_resize_redraw_everything():
    frame, out = _frame()
    frame.show(Block.text("ab"))
    assert out[-1].startswith(CLEAR)
    frame.show(Block.text("abc"))
    assert out[-1].startswith(CLEAR)
    frame.invalidate()
    frame.show(Block.text("abc"))
    assert out[-1].startswith(CLEAR)


def test_rows_a_shorter_screen_no_longer_has_are_blanked():
    frame, out = _frame()
    frame.show(Block.text("a\nb\nc"))
    frame.show(Block.text("a\nb"))
    assert out[-1] == "\x1b[3;1H\x1b[2K"


def test_a_synchronized_frame_is_wrapped_whole():
    out: list[str] = []
    frame = Frame(out.append, profile=Profile.NO_TTY)
    frame.show(Block.text("x"))
    assert out[-1].startswith(SYNC_BEGIN) and out[-1].endswith(SYNC_END)
