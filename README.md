# bewitch

A Python port of [Charm](https://charm.land)'s [Lip Gloss](https://github.com/charmbracelet/lipgloss)
and [charmtone](https://github.com/charmbracelet/x/tree/main/exp/charmtone), made
because we liked them so much — with the drawn parts of
[Bubbles](https://github.com/charmbracelet/bubbles) and the look of
[Crush](https://github.com/charmbracelet/crush) on top.

**Not affiliated with or endorsed by Charm.** The module names are theirs on
purpose: `bewitch.lipgloss` is our port of Lip Gloss, `bewitch.charmtone` of
charmtone, `bewitch.bubbles` of the drawing half of Bubbles. Naming them so is
the credit — Charm's work is MIT-licensed, we copied it into another language,
and we would rather say so than file the names off. See
[THIRD_PARTY.md](https://github.com/gsfernandes81/bewitch/blob/main/THIRD_PARTY.md).

```python
from bewitch import bubbles, charmtone
from bewitch.lipgloss import Style, rounded_border

card = (
    Style()
    .foreground(charmtone.Butter)
    .background(charmtone.Charple)
    .padding(0, 1)
    .border(rounded_border())
    .border_foreground(charmtone.Dolly)
    .width(30)
)
print(card.render("Chillhop Essentials · Winter 2025"))
print(bubbles.header("ytq", ["lofi hip hop", "20"], width=40))
```

## What it is, and what it is not

bewitch draws. It does not read keys, run an event loop or hold state —
the app does that, on whatever TUI library it uses (blessed, for ytq and dlq),
and bewitch gives it Crush's look. A render is a `Block` of styled spans rather than a string full
of escape sequences, so the same render can go to:

| Adapter | For |
|---|---|
| `bewitch.ansi` | `print()`, and anything that takes ANSI strings (blessed, Rich's `Text.from_ansi`) |
| `bewitch.screen.Frame` | full-screen apps, on blessed or anything that can write to the terminal: a whole screen per frame, only the changed lines written, nothing at all when nothing changed |
| *(planned)* Rich | Textual and Rich |

## Modules

| Module | Ports | What it does |
|---|---|---|
| `bewitch.lipgloss` | Lip Gloss v2.0.6 | `Style` (colours, attributes, padding, margin, borders, width, height, alignment), the border sets, `join_horizontal` / `join_vertical` / `place`, `Canvas`, `width` / `truncate`, `blend_1d` |
| `bewitch.charmtone` | charmtone v0.1.0 | Charm's 70 colours, Charm's names (`charmtone.Charple`), Charm's groups |
| `bewitch.bubbles` | Bubbles v2.2.1 (drawing only) | spinners, help line, progress bar, paginator, scrollbar, list rows; from huh, the checkbox; and, from Crush, the header band, section rules, dialog titles, labels and status rows |
| `bewitch.colorprofile` | colorprofile v0.4.3 | truecolor / 256 / 16 / none, from the environment; colours fitted to each |
| `bewitch.theme` | — | colours by role (`primary`, `fg_muted`, `separator`…), Crush's mapping by default |
| `bewitch.glyphs` | — | the glyphs Crush draws with, each tested on a phone, each with an ASCII stand-in |

## The house style

[docs/house-style.md](https://github.com/gsfernandes81/bewitch/blob/main/docs/house-style.md) is the standard every screen built on
bewitch follows: the anatomy of a screen, colour by role, selection, marks,
dialogs, glyphs, how things give way at 32 columns, and how to move a curses
screen over.

## The gallery

```sh
python -m bewitch              # at this terminal's width
python -m bewitch --width 40   # at 40 columns
python -m bewitch --color 256  # as a 256-colour terminal would show it
```

Draws every piece in the terminal you run it in. Every line ends at the same
column, so a glyph your font draws two columns wide shows up as a ragged
right edge on its line. Run it on the device a screen is for — that is the
test no suite can run.

## Colour

Detection follows Charm's `colorprofile`, plus three rules:

- **Termux is truecolor**, although it reports `TERM=xterm-256color`.
- **`BEWITCH_COLOR`** (`truecolor`, `256`, `16`, `ascii`, `none`) overrides
  everything, and **`NO_COLOR`** is honoured.
- **Without colour, a background becomes reverse video**, so a selection bar
  never disappears with the colour.

## Using it

bewitch is standard library only. Install it from PyPI:

```sh
pip install bewitch
```

or use it from a checkout — put the checkout on `sys.path`, the way nibbles
finds it — or install that with `pip install -e .`.

## Releasing

A push to `main` that changes `version` in `pyproject.toml` to one PyPI does
not have yet is a release: `.github/workflows/release.yml` runs the suite,
builds, publishes through PyPI's trusted publishing (no token is stored
anywhere) and tags `v<version>`. Bump `__version__` in `bewitch/__init__.py`
with it; a test holds the two together.

## Developing

```sh
make dev     # uv sync: pytest and hypothesis into .venv
make test    # the suite (also .githooks/checks.sh, which the pre-push hook runs)
make lint    # ruff
make golden  # re-record the reference renders after a deliberate visual change
```

Enable the hook once per clone: `git config core.hooksPath .githooks`.

## Licence

MIT. Lip Gloss, charmtone, Bubbles and colorprofile are MIT-licensed by
Charmbracelet, Inc.; their notice is in [THIRD_PARTY.md](https://github.com/gsfernandes81/bewitch/blob/main/THIRD_PARTY.md).
