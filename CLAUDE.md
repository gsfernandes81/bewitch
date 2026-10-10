# bewitch — working notes for Claude

A Python port of Charm's Lip Gloss and charmtone, plus the drawn half of
Bubbles and the look of Crush. Its first users are `ytq` and `dlq`, which run
in Termux on a phone, in a terminal about 40 columns wide in portrait — so
every layout rule here is about fitting a narrow screen exactly. Started
2026-10-10.

Decisions that travel with this code:

- **Charm's names are kept on purpose.** `bewitch.lipgloss`,
  `bewitch.charmtone`, `bewitch.bubbles`, with Lip Gloss's API in Python
  spelling (`NewStyle().Bold(true)` → `Style().bold()`) and charmtone's tones
  in Charm's own spelling (`charmtone.Charple`). The owner's position: copying
  a style but not its name is ripping Charm off; copying both says plainly
  that we ported their MIT work because we liked it. So the README's first
  lines credit Charm and say "not affiliated", `THIRD_PARTY.md` carries the
  MIT notices, and each module's docstring names the version it follows.
  **No Crush code is copied** — Crush is FSL-1.1-MIT, not MIT. `theme.py` and
  `bubbles/crush.py` are written from how Crush looks; anything that needed
  code came from the MIT libraries.
- **A render is a `Block`, never a string of escape sequences.** Every line
  is a tuple of `Span`s, each with a `Pen`, and every line is exactly
  `block.width` columns. Escape sequences are written only by an adapter at
  the very end (`bewitch.ansi` today). That is what lets one render go to
  `print()`, blessed, curses (which corrupts on raw escapes) or Rich. Do not
  add a code path that returns pre-escaped strings from a style or recipe.
- **A `Pen` attribute of `None` means inherit, never off.** An inner span with
  no background sits on the outer background. This is the one place bewitch
  is deliberately *better* than Lip Gloss, whose nested renders end in a reset
  and lose the outer style; keep it.
- **Width is exact.** As in Lip Gloss v2, `width` counts border and padding,
  not margin. Text is wrapped to fit; a `Block` rendered into a narrower style
  is cut, not wrapped; a wide character in a one-column room is dropped. Every
  recipe in `bewitch.bubbles` returns exactly the width it was given, and
  gives up decoration before words (the header's `╱` band shrinks to
  `MIN_DIAGONALS` before the details are cut, and the details go before the
  name). The layout tests check this as a property over text that mixes
  ASCII, ambiguous-width glyphs, wide CJK and combining marks.
- **East Asian Ambiguous is one column** (`│ … • ✓ ╱`), because that is how
  Termux draws them, checked on the phone. `char_width` is the one place that
  decides a character's width; do not measure with `len()`.
- **Glyphs were tested on the phone, and three failed:** `⏸` (an orange
  emoji), `✕` and `⟳` (taken from a fallback font). `glyphs.EXCLUDED` keeps
  them as data so a test can hold the line. A new glyph is tried in Termux
  with `python -m bewitch` before it goes in.
- **Colour detection is colorprofile's, plus three rules:** `TERMUX_VERSION`
  means truecolor (Termux says `xterm-256color` but draws 24-bit colour);
  `BEWITCH_COLOR` overrides everything; and under the ASCII profile the ANSI
  adapter turns a background into reverse video, so a selection bar never
  vanishes with the colour.
- **Go's arithmetic where it differs from Python's.** Positions round half
  away from zero (`floor(x + 0.5)`), not banker's rounding, and
  `convert_256`'s grey index truncates toward zero as Go's integer division
  does. Both are commented where they happen; a "simplification" to Python's
  default would move things by a cell.
- **Gradients and colour distance are in CIELAB**, as Lip Gloss's `Blend1D`
  is. `convert_256` measures "nearer" in Lab where x/ansi uses HSLuv — a
  documented deviation, not an oversight.
- **Recipes hold no state and run no timers.** A spinner is frames and a
  rate; the app's event loop decides when to draw. That keeps an idle screen
  silent, which ytq treats as a property worth a test.
- **Standard library only.** The phone uses this from a checkout beside ytq
  and dlq, with nothing installed. A dependency would need a very good reason.

## Checks

`make test` = `make check` = `.githooks/checks.sh`, which the pre-push hook
runs. Offline, a few seconds.

- `test_color.py` — parsing, Lab round-trips, `blend_1d` against Lip Gloss's
  edge cases, and charmtone's values spot-checked against Charm's source.
- `test_colorprofile.py` — detection over a table of environments, and
  conversion landing inside each profile.
- `test_layout.py` — the layout guarantees as properties: every render is a
  rectangle, a set width is the width you get, cuts and wraps never run past
  their limit, a wrap never loses a word, joins add up.
- `test_output.py` — the ANSI adapter, every recipe at exactly its width,
  the glyph rules, and the **reference renders**: byte-for-byte against
  `tests/golden/*.ans`. A deliberate visual change is re-recorded with
  `make golden`, and the diff of those files *is* the visual change — read it
  before committing it.

The test no suite can run is `python -m bewitch` on the phone: every line
ends at the same column, so a glyph drawn two columns wide shows as a ragged
edge on its line.

## What is next

- **A blessed adapter**: draw a frame of positioned lines and write only the
  lines that changed, so an unchanged frame writes nothing. ytq and dlq move
  from curses to blessed on top of it, on their `bewitched` branches, and are
  not merged without the owner's go-ahead.
- Curses and Rich adapters, when something needs them.
- Lip Gloss's `table`, `list` and `tree` sub-packages, `Blend2D`, hyperlinks.
