"""Colour detection, and fitting a colour to what was detected."""

from __future__ import annotations

import io

import pytest
from conftest import colors
from hypothesis import given
from hypothesis import strategies as st

from bewitch.color import Color
from bewitch.colorprofile import (
    Indexed,
    Profile,
    convert,
    convert_256,
    detect,
    env_profile,
    palette_color,
)

TC, C256, C16, ASCII, NONE = (
    Profile.TRUE_COLOR,
    Profile.ANSI256,
    Profile.ANSI,
    Profile.ASCII,
    Profile.NO_TTY,
)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"TERM": "xterm-256color"}, C256),
        ({"TERM": "xterm"}, C16),
        ({"TERM": "xterm-256color", "COLORTERM": "truecolor"}, TC),
        ({"TERM": "xterm-kitty"}, TC),
        ({"TERM": "screen-256color", "COLORTERM": "truecolor"}, C256),
        ({"TERM": "xterm-direct"}, TC),
        ({"TERM": "dumb"}, NONE),
        ({}, NONE),
        # Termux: 256color by TERM, truecolor in fact (checked on the phone).
        ({"TERM": "xterm-256color", "TERMUX_VERSION": "0.118.3"}, TC),
        ({"TERM": "xterm-256color", "NO_COLOR": "1"}, ASCII),
        ({"TERM": "xterm-256color", "NO_COLOR": "1", "TERMUX_VERSION": "1"}, ASCII),
        ({"TERM": "dumb", "CLICOLOR_FORCE": "1"}, C16),
    ],
)
def test_detection_reads_the_environment_as_colorprofile_does(env, expected):
    assert env_profile(env, isatty=True) == expected


@pytest.mark.parametrize("value", ["truecolor", "256", "16", "ascii", "none"])
def test_bewitch_color_wins_over_everything(value):
    env = {"TERM": "dumb", "NO_COLOR": "1", "BEWITCH_COLOR": value}
    expected = {"truecolor": TC, "256": C256, "16": C16, "ascii": ASCII, "none": NONE}
    assert env_profile(env, isatty=False) == expected[value]


def test_output_that_is_not_a_terminal_gets_no_escapes():
    env = {"TERM": "xterm-256color", "COLORTERM": "truecolor"}
    assert detect(io.StringIO(), env) == NONE
    assert detect(io.StringIO(), {**env, "TTY_FORCE": "1"}) == TC


def test_the_profiles_are_ordered_by_capability():
    assert NONE < ASCII < C16 < C256 < TC


@given(st.integers(16, 255))
def test_every_palette_colour_converts_to_itself(n):
    color = palette_color(Indexed(n))
    assert palette_color(convert_256(color)) == color


@given(colors)
def test_conversion_lands_inside_each_profile(color):
    assert convert(color, TC) == color
    assert 0 <= convert(color, C256).n <= 255
    assert 0 <= convert(color, C16).n <= 15
    assert convert(color, ASCII) is None
    assert convert(color, NONE) is None


def test_near_greys_go_to_the_grey_ramp_and_saturated_colours_do_not():
    assert convert_256(palette_color(Indexed(240))).n == 240
    # Between the cube's greys (0x5f and 0x87), the ramp is nearer.
    assert convert_256(Color(0x7A, 0x7A, 0x7A)).n in (243, 244)
    # On one of them, the cube's own grey wins.
    assert convert_256(Color(0x87, 0x87, 0x87)).n == 102
    assert 16 <= convert_256(palette_color(Indexed(99))).n <= 231


def test_very_dark_greys_do_not_index_below_the_ramp():
    # Go truncates (0 - 3) / 10 to 0; Python's // would floor it to -1.
    for v in range(0, 8):
        assert convert_256(Color(v, v, v)).n in (16, 232)


def test_basic_colours_convert_to_their_own_index_under_16_colours():
    assert convert(palette_color(Indexed(9)), C16) == Indexed(9)
    assert convert(Indexed(196), C16) == Indexed(9)
