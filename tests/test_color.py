"""Colours, and the palette: parsing, Lab, blending, and charmtone's values."""

from __future__ import annotations

import pytest
from conftest import colors
from hypothesis import given
from hypothesis import strategies as st

from bewitch import charmtone
from bewitch.color import Color, to_color
from bewitch.lipgloss import blend_1d


@pytest.mark.parametrize("spelling", ["#6B50FF", "#6b50ff", "6B50FF", " #6b50ff "])
def test_every_spelling_of_a_hex_parses_to_the_same_colour(spelling):
    assert Color.parse(spelling) == Color(0x6B, 0x50, 0xFF)


def test_short_hex_doubles_each_digit():
    assert Color.parse("#fa0") == Color(0xFF, 0xAA, 0x00)


@pytest.mark.parametrize("bad", ["", "#12", "#12345", "red", "#ggg"])
def test_what_is_not_a_hex_colour_is_refused(bad):
    with pytest.raises(ValueError):
        Color.parse(bad)


def test_a_tone_equals_the_same_colour_parsed_by_hand():
    # A test that compared classes here would be asserting about a name.
    assert charmtone.Charple == Color.parse("#6B50FF")
    assert hash(charmtone.Charple) == hash(Color.parse("#6B50FF"))
    assert to_color("#6B50FF") == charmtone.Charple


@given(colors)
def test_hex_round_trips(color):
    assert Color.parse(color.hex) == color


@given(colors)
def test_lab_round_trips_to_the_same_bytes(color):
    assert Color.from_lab(*color.lab()) == color


@given(colors, colors)
def test_a_blend_starts_and_ends_on_its_stops(a, b):
    assert a.blend(b, 0) == a
    assert b == a.blend(b, 1)


@given(colors, colors, st.floats(0, 1))
def test_a_blend_never_lands_further_from_both_ends_than_they_are_apart(a, b, t):
    # Lab is not perfectly closed under the sRGB gamut clamp, so allow the
    # clamp's rounding; the point is no blend wanders off the line.
    mid = a.blend(b, t)
    apart = a.distance(b)
    assert a.distance(mid) <= apart + 2.5
    assert b.distance(mid) <= apart + 2.5


def test_blend_1d_matches_lip_gloss_on_the_edge_cases():
    assert blend_1d(0, "#000000", "#ffffff") == []
    assert blend_1d(2, "#000000", "#ffffff") == [Color(0, 0, 0), Color(255, 255, 255)]
    assert blend_1d(3, "#123456") == [Color.parse("#123456")] * 3
    assert blend_1d(3, None, None) == []


@given(st.integers(3, 80), st.lists(colors, min_size=2, max_size=5))
def test_blend_1d_gives_exactly_the_steps_asked_for_starting_on_the_first_stop(n, stops):
    out = blend_1d(n, *stops)
    if n <= len(stops):
        assert out == stops[:n]
    else:
        assert len(out) == n
        assert out[0] == stops[0]
        # Lip Gloss's arithmetic: a segment given one step shows only its
        # start, so the last stop is reached only when every segment has two.
        if n >= 2 * (len(stops) - 1):
            assert out[-1] == stops[-1]


# charmtone ---------------------------------------------------------------


def test_charmtone_has_charms_seventy_tones_with_unique_names():
    assert len(charmtone.KEYS) == 70
    assert len({t.name for t in charmtone.KEYS}) == 70


@pytest.mark.parametrize(
    ("tone", "hex_value"),
    [
        (charmtone.Charple, "#6B50FF"),
        (charmtone.Dolly, "#FF60FF"),
        (charmtone.Pepper, "#201F26"),
        (charmtone.BBQ, "#2D2C36"),
        (charmtone.Butter, "#FFFAF1"),
        (charmtone.Julep, "#00FFB2"),
        (charmtone.Cumin, "#BF976F"),
        (charmtone.Ice, "#00FFFC"),
    ],
)
def test_spot_values_match_charms_source(tone, hex_value):
    assert tone.hex == hex_value


def test_the_groups_are_drawn_from_the_keys_in_charms_order():
    assert charmtone.SPECTRUM[0] is charmtone.Cumin
    assert charmtone.SPECTRUM[-1] is charmtone.Zest
    for group in (
        charmtone.NEUTRALS,
        charmtone.CHARPLES,
        charmtone.ADDITIONS,
        charmtone.DELETIONS,
        charmtone.PRIMARY,
        charmtone.SECONDARY,
    ):
        assert set(group) <= set(charmtone.KEYS)


def test_lookup_by_name_and_by_hex():
    assert charmtone.by_name("charple") is charmtone.Charple
    assert charmtone.name_from_hex("#ff60ff") == "Dolly"
    assert charmtone.name_from_hex("#123456") == ""
    assert str(charmtone.Charple) == "Charple"
