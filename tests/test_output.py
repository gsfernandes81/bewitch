"""The ANSI adapter, the recipes, the glyph rules and the reference renders."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from conftest import lines, widths
from hypothesis import given
from hypothesis import strategies as st

from bewitch import ansi, bubbles, glyphs
from bewitch.__main__ import gallery, results_screen
from bewitch.colorprofile import Profile
from bewitch.lipgloss import Block, Style, string_width
from bewitch.theme import CHARM

ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
GOLDEN = Path(__file__).parent / "golden"


def _strip(text: str) -> str:
    return ESCAPE.sub("", text)


# The ANSI adapter ----------------------------------------------------------


@given(lines, st.sampled_from(list(Profile)))
def test_stripping_the_escapes_gives_back_exactly_the_text(text, profile):
    block = (
        Style().foreground(CHARM.primary).background(CHARM.bg_base).bold().render(text)
    )
    assert _strip(ansi.render(block, profile)) == block.plain()


def test_no_tty_writes_no_escapes_at_all():
    block = Style().foreground(CHARM.primary).bold().render("x")
    assert ansi.render(block, Profile.NO_TTY) == "x"


def test_each_styled_line_resets_at_its_end():
    block = Style().foreground(CHARM.primary).render("a\nb")
    for line in ansi.render(block, Profile.TRUE_COLOR).split("\n"):
        assert line.endswith(ansi.RESET)


@pytest.mark.parametrize(
    ("profile", "pattern"),
    [
        (Profile.TRUE_COLOR, r"\x1b\[0;38;2;107;80;255m"),
        (Profile.ANSI256, r"\x1b\[0;38;5;\d+m"),
        (Profile.ANSI, r"\x1b\[0;(3[0-7]|9[0-7])m"),
    ],
)
def test_colours_are_written_for_the_profile(profile, pattern):
    out = ansi.render(Style().foreground(CHARM.primary).render("x"), profile)
    assert re.match(pattern, out)


def test_under_ascii_a_background_becomes_reverse_video():
    # A selection bar is a background; with colour stripped it must not
    # vanish, or the list loses its cursor.
    row = bubbles.list_item("pick me", 20, selected=True)
    out = ansi.render(row, Profile.ASCII)
    assert "\x1b[0;7m" in out
    assert "38;" not in out and "48;" not in out


# Recipes -------------------------------------------------------------------


@given(widths, lines, st.lists(lines, max_size=4))
def test_the_header_is_always_exactly_its_width(width, name, details):
    assert bubbles.header(name or "x", details, width).width == width


@given(widths)
def test_the_header_cuts_details_before_the_band_goes_below_three(width):
    block = bubbles.header("ytq", ["a very long query that will not fit", "20"], width)
    text = block.plain()
    assert text.startswith(" ytq ")
    assert text.count(glyphs.DIAGONAL) >= 3


@given(widths, lines, st.none() | lines)
def test_a_section_is_always_exactly_its_width(width, title, info):
    assert bubbles.section(title, width, info=info).width == width


@given(widths, lines)
def test_a_dialog_title_is_always_exactly_its_width(width, title):
    assert bubbles.dialog_title(title, width).width == width


@given(widths, lines, st.none() | lines, st.booleans(), st.sampled_from(["", "✓"]))
def test_a_list_item_is_always_exactly_its_width(width, title, sub, selected, mark):
    block = bubbles.list_item(title, width, subtitle=sub, selected=selected, mark=mark)
    assert block.width == width
    assert block.height == (1 if sub is None else 2)


def test_a_mark_never_shifts_the_title():
    plain = bubbles.list_item("title", 20).plain()
    marked = bubbles.list_item("title", 20, mark="✓").plain()
    assert plain.index("title") == marked.index("title")


@given(st.integers(0, 80), lines, st.booleans(), st.booleans())
def test_a_checkbox_is_always_exactly_its_width(width, label, checked, boxed):
    block = bubbles.checkbox(label, checked, width, boxed=boxed)
    assert block.width == width
    assert block.height == (3 if boxed else 1)
    for line in block.lines:
        assert string_width("".join(s.text for s in line)) == width


@given(st.integers(1, 80), lines, st.booleans(), st.booleans())
def test_a_checkbox_cuts_its_label_before_its_mark(width, label, checked, boxed):
    mark = glyphs.CHECK if checked else glyphs.BULLET
    assert mark in bubbles.checkbox(label, checked, width, boxed=boxed).plain()


@given(st.integers(0, 80), lines, st.booleans())
def test_ticking_a_checkbox_never_shifts_its_label(width, label, boxed):
    ticked = bubbles.checkbox(label, True, width, boxed=boxed).plain()
    unticked = bubbles.checkbox(label, False, width, boxed=boxed).plain()
    assert ticked.replace(glyphs.CHECK, glyphs.BULLET) == unticked.replace(
        glyphs.CHECK, glyphs.BULLET
    )


def test_without_colour_a_checkbox_still_says_whether_it_is_ticked():
    for boxed in (False, True):
        ticked = ansi.render(bubbles.checkbox("go", True, 12, boxed), Profile.ASCII)
        unticked = ansi.render(bubbles.checkbox("go", False, 12, boxed), Profile.ASCII)
        assert glyphs.CHECK in ticked and "\x1b[0;1m" in ticked
        assert glyphs.BULLET in unticked and "\x1b[0;1m" not in unticked


@given(
    widths,
    st.lists(
        st.tuples(
            st.sampled_from(["↑↓", "⏎", "q", "/", "esc", "tab"]), lines.map(str.strip)
        ),
        max_size=6,
        unique_by=lambda pair: pair[0],
    ),
)
def test_help_adds_pairs_whole_or_says_it_stopped(width, bindings):
    block = bubbles.short_help(bindings, width)
    text = block.plain().rstrip()
    assert block.width == width
    shown = [key for key, _ in bindings if key in text]
    if text and len(shown) < len(bindings):
        assert text.endswith(glyphs.ELLIPSIS) or string_width(text) >= width - 2


def test_help_gives_up_the_dot_before_it_gives_up_a_pair():
    pairs = [("↑↓", "pick"), ("⏎", "quality"), ("/", "new"), ("q", "back")]
    roomy = bubbles.short_help(pairs, 40).plain()
    tight = bubbles.short_help(pairs, 33).plain()
    assert "•" in roomy
    assert "•" not in tight and tight.rstrip().endswith("q back")


@given(widths, st.floats(0, 1))
def test_the_progress_bar_is_exactly_its_width(width, percent):
    assert bubbles.progress_bar(percent, width).width == width


def test_the_progress_bar_fills_further_as_percent_grows():
    counts = [
        bubbles.progress_bar(p / 10, 40).plain().count(glyphs.BAR_FULL) for p in range(11)
    ]
    assert counts == sorted(counts)
    assert counts[0] == 0


@given(st.integers(1, 30), st.integers(0, 200), st.integers(1, 50), st.integers(0, 200))
def test_the_scroll_thumb_stays_on_its_track(height, total, visible, offset):
    start, length = bubbles.scroll_thumb(height, total, visible, offset)
    assert 1 <= length <= height
    assert start >= 0 and start + length <= height


@given(st.integers(2, 30), st.integers(10, 200), st.integers(1, 9))
def test_the_thumb_is_at_the_top_first_and_the_bottom_last(height, total, visible):
    assert bubbles.scroll_thumb(height, total, visible, 0)[0] == 0
    start, length = bubbles.scroll_thumb(height, total, visible, total - visible)
    assert start + length == height


@given(st.integers(20, 80), lines, st.lists(lines, max_size=4), st.booleans())
def test_a_dialog_is_exactly_its_width_and_rounded(width, title, body, with_keys):
    keys = [("⏎", "ok"), ("esc", "back")] if with_keys else []
    box = bubbles.dialog(title or "x", body, width, keys=keys)
    assert box.width == width
    text = box.plain().split("\n")
    assert text[0].startswith("╭") and text[-1].startswith("╰")


@given(st.integers(20, 80), lines, st.integers(0, 50))
def test_a_wait_box_is_exactly_its_width(width, text, tick):
    assert bubbles.wait_box(text, tick, width).width == width


def test_spinner_frames_cycle():
    assert bubbles.spinner.Line.frame(5) == "/"
    assert bubbles.spinner.Dot.interval == pytest.approx(0.1)


# Glyph rules ---------------------------------------------------------------


def test_no_excluded_glyph_is_offered_or_drawn():
    offered = {g for g, _ in glyphs.GLYPHS.values()}
    drawn = gallery(40).plain()
    for bad in glyphs.EXCLUDED:
        assert bad not in offered
        assert bad not in drawn


def test_every_glyph_is_one_column_and_has_an_ascii_stand_in():
    for name, (glyph, fallback) in glyphs.GLYPHS.items():
        assert string_width(glyph) == 1, name
        assert fallback.isascii(), name
        assert glyphs.pick(name, ascii_only=True) == fallback


# The gallery and the reference renders -------------------------------------


@given(st.integers(32, 70))
def test_every_gallery_line_ends_at_the_same_column(width):
    block = gallery(width)
    assert block.width == width
    assert {string_width("".join(s.text for s in line)) for line in block.lines} == {
        width
    }


@pytest.mark.parametrize(
    ("name", "make", "profile"),
    [
        ("results-40-truecolor", lambda: results_screen(40), Profile.TRUE_COLOR),
        ("results-32-256", lambda: results_screen(32), Profile.ANSI256),
        ("results-40-ascii", lambda: results_screen(40), Profile.ASCII),
        ("gallery-40-truecolor", lambda: gallery(40), Profile.TRUE_COLOR),
    ],
)
def test_reference_renders_are_unchanged(name, make, profile):
    """Byte-for-byte against a saved render. A deliberate visual change is
    re-recorded with ``make golden``; then look at the diff before committing
    it, because the diff *is* the visual change."""
    out = ansi.render(make(), profile) + "\n"
    path = GOLDEN / f"{name}.ans"
    if os.environ.get("BEWITCH_UPDATE_GOLDEN") == "1":
        GOLDEN.mkdir(exist_ok=True)
        path.write_text(out, encoding="utf-8")
    assert path.exists(), f"no reference render yet: run `make golden` ({path.name})"
    assert out == path.read_text(encoding="utf-8")


def test_a_block_prints_as_its_ansi_render():
    block = Block.text("hello")
    assert str(block) == ansi.render(block)
