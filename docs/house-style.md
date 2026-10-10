# House style

How a screen built on bewitch looks, so that every TUI built on it looks like
the same family — and like Charm's. This is the standard; `python -m bewitch`
is what it looks like. Where this page and the gallery disagree, fix one of
them.

The look is Crush's. The rules underneath it are ours: the screens this was
written for run on a phone, in a terminal about 40 columns wide, over a metered
connection, and every rule below holds at **32 columns** and up.

## A screen, top to bottom

```
 ytq ╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱ lofi hip hop • 20      header
                                           (blank)
Results ────────────────── ~ dates approx   section
                                           (blank)
   lofi hip hop radio - beats to rel…  │   body: list rows,
   Lofi Girl · live                    ┃   scrollbar in the
   Chillhop Essentials · Winter 2025   ┃   last column
 ✓ lofi hip hop mix - beats to sleep…  │
                                           (blank)
  720p  ⣾ 41/120 MiB · 4m left              status
                                           (blank)
↑↓ pick • ⏎ quality • / new • q back        help
```

| Part | Recipe | Rule |
|---|---|---|
| Header | `bubbles.header(name, details, width)` | One per screen, on the first row. The app's name in the secondary → primary gradient, bold; the `╱` band; then what this screen is *about* (the query, the item, the count) in muted grey. Never a reverse-video title bar. |
| Section | `bubbles.section(title, width, info)` | Names a block of content. Title in the most subtle grey, a `─` rule in the separator colour, optional info at the right. A blank row above and below. |
| Body | `bubbles.list_item(...)`, plain text, `Style` | The content. Body text is `fg_base`; secondary lines `fg_more_subtle`; tertiary `fg_most_subtle`. |
| Status | `bubbles.tag`, `bubbles.status`, a spinner | What is happening now: a running download, a fetch. One row, just above the help. |
| Help | `bubbles.short_help(pairs, width)` | The last row. Keys a shade lighter than their words, `•` between pairs, dropped to two spaces before a pair is dropped. The way out (`q back`, `esc quit`) is the last pair and the one that must survive. |

## Colour

Always by role, from `bewitch.theme` — never a tone, never a hex, in app code.

| Role | For |
|---|---|
| `primary` | the selection bar, dialog borders, the header band |
| `secondary` | gradient ends, the scrollbar thumb, spinners |
| `fg_base` / `fg_subtle` / `fg_more_subtle` / `fg_most_subtle` | text, stepping back: body, section-adjacent, secondary lines, tertiary lines |
| `on_primary` | text on the selection bar and on primary labels |
| `separator` | rules, help separators, scrollbar tracks |
| `success` / `warning` / `error` / `info` | what they say — and never the only thing saying it |
| `bg_less_visible` | a panel lifted off the background (a dialog's content area) |

Grey does the work faint text used to do. Do not reach for `A_DIM`/`faint`:
a terminal's faint is a guess at grey, and `fg_more_subtle` is the grey.

Colour is never the only signal: a mark has a glyph (`✓`), a state has a word,
a label has text. Without colour (`NO_COLOR`, `BEWITCH_COLOR=ascii`) the
selection bar becomes reverse video by itself, and everything else still reads.

## Selection

The selected row is a **filled bar in `primary`**, text in `on_primary`, as wide
as the content it selects — both lines of a two-line row. `list_item(selected=
True)` draws it. Never reverse video in a themed screen; never an arrow or a
`>` cursor in a list.

## Marks and state

| Meaning | Draw |
|---|---|
| already have it / done | `✓` in `success`, the row's text dimmed a step |
| failed | `×` in `error` |
| pending / in progress | `●` in `success_most_subtle`, or a spinner in `secondary` |
| on / off choice | `◉` / `○` |
| a word that must stand out | `bubbles.tag(text, kind)`: ` 720p `, ` PAID `, ` ERROR ` |

A mark column is kept even when empty, so marking a row never shifts its text.

## Dialogs and boxes

Anything drawn over a screen — a message, a confirmation, a wait — is a
**rounded border in `primary`**, `bubbles.dialog_title(title, inner_width)` on
its first row inside, its body in `fg_base`, its keys in `short_help` on its last
row. Composed over the screen with a `Canvas`, never by clearing the screen
first: what was behind it stays visible behind it.

A wait (a fetch, a probe) is the same box with a spinner (`spinner.Dot`, in
`secondary`) and one line saying what is being waited for.

## Glyphs

Only those in `bewitch.glyphs` — each was drawn on the phone first. `⏸`, `✕`
and `⟳` are out (`glyphs.EXCLUDED` says why). No emoji, no `⚠`. A new glyph is
tried in Termux with `python -m bewitch` before it goes in, and added to
`glyphs.py` with its ASCII stand-in.

## Size

- Every line of every screen fits **32 columns** and up, and is exactly the
  width it was laid out for. Recipes guarantee their own width; a screen's
  layout tests should sweep widths, not pick one.
- Things give way in this order: decoration (the band, blank rows, the dot in
  the help), then secondary text (channel names, descriptions), then whole
  optional items (a help pair other than the way out). Never the way out, and
  never the one fact a row exists to show.
- Two-line list rows below 72 columns; one-line rows with columns at 72 and up.

## Motion and touch

- An idle screen writes nothing. Draw through `screen.Frame` (or `cursed`),
  which writes only changed lines and nothing at all when nothing changed.
  Animate only what is selected (the marquee on the cursor row) or what is
  running (a spinner), and only while it is.
- A flick scrolls; only a keypress acts. Ask for wheel events only
  (`mousemask(BUTTON4_PRESSED | BUTTON5_PRESSED)`), so a tap is never a key.

## Moving a curses screen to this

| Was | Becomes |
|---|---|
| a reverse-video title bar | `bubbles.header` |
| a dim line saying what is shown | `bubbles.section(title, width, info=…)` |
| `A_REVERSE` on the cursor row | `list_item(selected=True)` or a primary-filled row |
| `A_DIM` text | `fg_more_subtle` / `fg_most_subtle` |
| `A_BOLD` emphasis | `fg_base` + bold, or a tag if it is a state |
| curses colour pairs (green/yellow/red/cyan) | `success` / `warning` / `error` / `primary` |
| a hint string at the bottom | `short_help(pairs, width)` with the same pairs, the way out last |
| a box drawn with `+-|` or cleared space | a rounded `Style` box with `dialog_title` |
| `=` against `·` progress | `bubbles.progress_bar` (`█`/`░`, both drawn one column wide on the phone) |

`win.draw(y, x, block)` puts a bewitch render on a `cursed` window; the screen's
loop, keys and logic do not change when its drawing does.
