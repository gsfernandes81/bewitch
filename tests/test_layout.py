"""Measuring, cutting, wrapping, styling and joining: the layout guarantees.

The properties here are the ones a screen is built on. A render is a
rectangle; a width that is set is the width you get; a cut never runs past
its limit; a wrap never loses a word. Each is checked over text that mixes
the four kinds of character that measure differently.
"""

from __future__ import annotations

import pytest
from conftest import colors, lines, texts
from hypothesis import given
from hypothesis import strategies as st

from bewitch import charmtone
from bewitch.lipgloss import (
    BOTTOM,
    CENTER,
    TOP,
    Block,
    Pen,
    Span,
    Style,
    hidden_border,
    join_horizontal,
    join_vertical,
    normal_border,
    place,
    rounded_border,
    string_width,
    thick_border,
    truncate,
    width,
)
from bewitch.lipgloss._cells import to_row, wrap_row


def _rectangular(block: Block) -> bool:
    return all(sum(s.width for s in line) == block.width for line in block.lines)


# Measuring and cutting ---------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [("abc", 3), ("日本", 4), ("é", 1), ("│…•✓╱", 5), ("", 0), ("a\tb", 2)],
)
def test_width_counts_terminal_columns(text, expected):
    # Ambiguous-width glyphs are one column, as Termux draws them; a tab is
    # a control character and zero until a Style expands it.
    assert string_width(text) == expected


def test_width_of_several_lines_is_the_widest():
    assert width("ab\nabcd\n") == 4


@given(lines, st.integers(0, 40), st.sampled_from(["", "…", "..."]))
def test_a_cut_never_runs_past_its_limit(text, limit, tail):
    assert string_width(truncate(text, limit, tail)) <= limit


@given(lines, st.integers(1, 40))
def test_a_cut_keeps_the_start_and_marks_what_it_dropped(text, limit):
    cut = truncate(text, limit, "…")
    if string_width(text) <= limit:
        assert cut == text
    else:
        assert cut.endswith("…")
        assert text.startswith(cut[:-1])


@given(lines, st.integers(2, 40))
def test_a_wrap_never_runs_past_its_limit_and_never_loses_a_word(text, limit):
    wrapped = wrap_row(to_row(text), limit)
    for row in wrapped:
        assert sum(string_width(ch) for ch, _ in row) <= limit
    kept = "".join(ch for row in wrapped for ch, _ in row if ch != " ")
    assert kept == text.replace(" ", "")


def test_a_wrap_does_not_break_at_a_hyphen():
    wrapped = wrap_row(to_row("see a-very-long here"), 12)
    assert ["".join(ch for ch, _ in r) for r in wrapped] == ["see", "a-very-long", "here"]


# Styles ------------------------------------------------------------------


styles = st.builds(
    lambda fg, bg, bold, pad, margin, border, w, h, align: (
        Style()
        .foreground(fg)
        .background(bg)
        .bold(bold)
        .padding(*pad)
        .margin(*margin)
        .border(border)
        .width(w)
        .height(h)
        .align(align, align)
    ),
    st.none() | colors,
    st.none() | colors,
    st.booleans(),
    st.tuples(*[st.integers(0, 3)] * 4),
    st.tuples(*[st.integers(0, 2)] * 4),
    st.sampled_from([normal_border(), rounded_border(), thick_border(), hidden_border()]),
    st.integers(0, 50),
    st.integers(0, 8),
    st.sampled_from([TOP, CENTER, BOTTOM, 0.3]),
)


@given(styles, texts)
def test_every_render_is_a_rectangle(style, text):
    assert _rectangular(style.render(text))


@given(styles, texts)
def test_a_set_width_is_the_width_you_get(style, text):
    # Lip Gloss v2's rule: width counts border and padding, not margin.
    # Below the frame itself there is no room for text, and the frame wins.
    p = style._p
    block = style.render(text)
    margins = p.margin[1] + p.margin[3]
    frame = style.get_horizontal_frame_size() - margins
    if p.width >= frame + 1:
        assert block.width == p.width + margins


@given(styles, texts)
def test_a_set_height_is_a_floor(style, text):
    p = style._p
    block = style.render(text)
    assert block.height >= p.height + p.margin[0] + p.margin[2]


@given(styles, texts, st.integers(1, 30), st.integers(1, 6))
def test_max_size_is_a_ceiling(style, text, max_w, max_h):
    block = style.max_width(max_w).max_height(max_h).render(text)
    assert block.width <= max_w
    assert block.height <= max_h


def test_a_border_and_padding_add_their_size():
    block = Style().padding(1, 2).border(rounded_border()).render("hi")
    assert (block.width, block.height) == (2 + 4 + 2, 1 + 2 + 2)
    assert block.plain().splitlines()[0] == "╭──────╮"


def test_css_shorthand_matches_lip_gloss():
    s = Style().padding(1, 2, 3)
    assert s._p.padding == (1, 2, 3, 2)
    with pytest.raises(TypeError):
        Style().padding(1, 2, 3, 4, 5)


def test_naming_one_border_side_turns_the_others_off():
    block = Style().border(normal_border()).border_bottom().render("hi")
    assert block.plain() == "hi\n──"


def test_an_inner_span_with_no_background_sits_on_the_outer_one():
    # Lip Gloss loses the outer style after a nested render's reset; here an
    # unset attribute inherits, which is what a person meant.
    outer = (
        Style()
        .background(charmtone.Charple)
        .render([Span("a"), Span("b", Pen(fg=charmtone.Dolly))])
    )
    pens = [span.pen for span in outer.lines[0]]
    assert all(p.bg == charmtone.Charple for p in pens)
    assert pens[-1].fg == charmtone.Dolly


def test_padding_takes_the_background_and_reverse():
    block = Style().background(charmtone.Charple).reverse().padding(0, 1).render("x")
    first = block.lines[0][0]
    assert first.pen.bg == charmtone.Charple and first.pen.reverse


def test_a_block_is_cut_to_a_narrower_style_rather_than_wrapped():
    inner = Style().render("abcdefghij")
    assert Style().width(4).render(inner).plain() == "abcd"


def test_a_block_cannot_be_mixed_with_text():
    with pytest.raises(TypeError):
        Style().render(Block.text("a"), "b")


def test_inline_drops_newlines_and_frame():
    block = Style().inline().padding(2).border(normal_border()).render("a\nb")
    assert block.plain() == "ab"


def test_tabs_become_four_spaces_by_default():
    assert Style().render("a\tb").plain() == "a    b"
    assert Style().tab_width(1).render("a\tb").plain() == "a b"


def test_render_joins_parts_with_a_space_as_lip_gloss_does():
    assert Style().render("a", "b").plain() == "a b"


# Joining and placing -----------------------------------------------------


blocks = st.builds(lambda t: Style().render(t), texts)


@given(st.lists(blocks, min_size=1, max_size=4), st.sampled_from([TOP, CENTER, BOTTOM]))
def test_join_horizontal_adds_widths_and_takes_the_tallest(parts, pos):
    joined = join_horizontal(pos, *parts)
    assert joined.width == sum(b.width for b in parts)
    assert joined.height == max(b.height for b in parts)
    assert _rectangular(joined)


@given(st.lists(blocks, min_size=1, max_size=4), st.sampled_from([TOP, CENTER, BOTTOM]))
def test_join_vertical_adds_heights_and_takes_the_widest(parts, pos):
    joined = join_vertical(pos, *parts)
    assert joined.height == sum(b.height for b in parts)
    assert joined.width == max(b.width for b in parts)
    assert _rectangular(joined)


def test_center_rounds_half_away_from_zero_as_go_does():
    # Two rows of slack: one above. Three: two above (round(1.5) = 2 in Go).
    tall = Block.text("\n\n\n")
    assert (
        join_horizontal(CENTER, tall, Block.text("x")).plain().split("\n")[2][-1] == "x"
    )
    taller = Block.text("\n\n")
    assert (
        join_horizontal(CENTER, taller, Block.text("x")).plain().split("\n")[1][-1] == "x"
    )


@given(blocks, st.integers(0, 60), st.integers(0, 10))
def test_place_fills_the_space_and_never_shrinks_the_block(block, w, h):
    placed = place(w, h, CENTER, CENTER, block)
    assert placed.width == max(w, block.width)
    assert placed.height == max(h, block.height)
    assert _rectangular(placed)
