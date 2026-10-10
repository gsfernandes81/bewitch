"""Shared strategies. The suite needs nothing else: bewitch is stdlib only,
reads no files and touches no network, so there is no environment to fake
beyond the variables colour detection reads, and those are passed in."""

from __future__ import annotations

import os

from hypothesis import HealthCheck, settings
from hypothesis import strategies as st

from bewitch.color import Color

settings.register_profile(
    "default", max_examples=200, suppress_health_check=[HealthCheck.too_slow]
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))

#: Text a screen actually meets: ASCII, the ambiguous-width glyphs Charm
#: draws with, wide CJK, and combining marks — the four kinds of character
#: that measure differently.
TEXT_CHARS = st.sampled_from(
    list("abcdefghij ABC -/.·") + list("│─╱…•✓●") + list("日本語") + ["\u0301"]
)
lines = st.text(TEXT_CHARS, max_size=60)
texts = st.text(TEXT_CHARS | st.just("\n"), max_size=60)
colors = st.builds(Color, st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
widths = st.integers(min_value=20, max_value=80)
