"""``python -m bewitch``: the gallery — every piece, drawn in this terminal.

Run it on the device a screen is for. It is the test that matters most and
the one no suite can run: whether *this* terminal, in *this* font, draws the
glyphs one column wide and the colours as they were meant. Every line it
prints ends at the same column; a ragged right edge names the glyph that
broke it.

    python -m bewitch                  at this terminal's width (32–60)
    python -m bewitch --width 40       at 40 columns
    python -m bewitch --color 256      as a 256-colour terminal would see it
"""

from __future__ import annotations

import argparse
import shutil
import sys

from bewitch import __version__, ansi, bubbles, charmtone, glyphs
from bewitch.bubbles import spinner
from bewitch.colorprofile import Profile, detect
from bewitch.lipgloss import (
    CENTER,
    LEFT,
    TOP,
    Block,
    Pen,
    Span,
    Style,
    join_horizontal,
    join_vertical,
    normal_border,
    rounded_border,
    thick_border,
)
from bewitch.theme import CHARM

_PROFILES = {
    "truecolor": Profile.TRUE_COLOR,
    "256": Profile.ANSI256,
    "16": Profile.ANSI,
    "ascii": Profile.ASCII,
    "none": Profile.NO_TTY,
}


def results_screen(width: int) -> Block:
    """The screen bewitch was made for: ytq's search results, Crush-styled."""
    t = CHARM
    hits = [
        ("lofi hip hop radio - beats to relax/study to", "Lofi Girl · live", ""),
        ("1 A.M Study Session - lofi hip hop", "Lofi Girl · ~4y · 1:01:02 · 98M", ""),
        ("Chillhop Essentials · Winter 2025", "Chillhop Music · ~9mo · 1:12:40", ""),
        ("lofi hip hop mix - beats to sleep to", "Dreamy · ~2w · 2:00:13 · 310K", "✓"),
        ("jazz hop café - morning coffee", "the bootleg boy · ~3y · 58:21", ""),
    ]
    body = width - 1  # the last column is the scrollbar
    items = [
        bubbles.list_item(
            title,
            body,
            subtitle=sub,
            selected=i == 2,
            mark=mark,
            mark_color=t.success if mark else None,
            dimmed=bool(mark),
        )
        for i, (title, sub, mark) in enumerate(hits)
    ]
    listing = join_vertical(LEFT, *items)
    bar = bubbles.scrollbar(listing.height, total=20, visible=5, offset=4)
    running = join_horizontal(
        TOP,
        Style().padding(0, 1).render(bubbles.tag("720p")),
        Style().foreground(t.secondary).render(spinner.Dot.frame(0)),
        Style().foreground(t.fg_subtle).render("41/120 MiB"),
        Style().foreground(t.separator).render(" · "),
        Style().foreground(t.fg_more_subtle).render("4m left"),
    )
    return join_vertical(
        LEFT,
        bubbles.header("ytq", ["lofi hip hop", "20"], width),
        Block.text(""),
        bubbles.section("Results", width, info="~ dates approx"),
        Block.text(""),
        join_horizontal(TOP, listing, bar),
        Block.text(""),
        running,
        Block.text(""),
        bubbles.short_help(
            [("↑↓", "pick"), ("⏎", "quality"), ("/", "new"), ("q", "back")], width
        ),
    )


def palette(width: int) -> Block:
    """Every charmtone, as a swatch and its name, as many to a line as fit."""
    cell = 3 + max(len(t.name) for t in charmtone.KEYS) + 1
    per_line = max(1, width // cell)
    rows = []
    tones = list(charmtone.KEYS)
    for i in range(0, len(tones), per_line):
        rows.append(
            join_horizontal(
                TOP,
                *(
                    Block([[Span("██", Pen(fg=tone)), Span(f" {tone.name:<{cell - 3}}")]])
                    for tone in tones[i : i + per_line]
                ),
            )
        )
    return join_vertical(LEFT, *rows)


def borders(width: int) -> Block:
    boxes = [
        Style().border(b).border_foreground(CHARM.primary).padding(0, 1).render(name)
        for name, b in (
            ("rounded", rounded_border()),
            ("normal", normal_border()),
            ("thick", thick_border()),
        )
    ]
    joined = join_horizontal(TOP, *(Style().margin_right(1).render(b) for b in boxes))
    return joined if joined.width <= width else join_vertical(LEFT, *boxes)


def pieces(width: int) -> Block:
    t = CHARM
    tags = join_horizontal(
        TOP,
        *(
            Style().margin_right(1).render(bubbles.tag(k.upper(), k))
            for k in ("error", "warn", "info", "success")
        ),
    )
    icons = Block(
        [
            [
                Span(glyphs.CHECK + " ", Pen(fg=t.success)),
                Span(glyphs.ERROR + " ", Pen(fg=t.error)),
                Span(glyphs.PENDING + " ", Pen(fg=t.success_most_subtle)),
                Span(glyphs.RADIO_ON + " ", Pen(fg=t.secondary)),
                Span(glyphs.RADIO_OFF + " ", Pen(fg=t.fg_subtle)),
                Span(glyphs.MODEL + " ", Pen(fg=t.fg_more_subtle)),
                Span(glyphs.THINKING + " ", Pen(fg=t.fg_more_subtle)),
                Span(glyphs.BORDER_THICK + " focused  ", Pen(fg=t.primary)),
                Span(glyphs.BORDER_THIN + " blurred", Pen(fg=t.primary)),
            ]
        ]
    )
    spins = Block(
        [
            [
                Span(
                    " ".join(
                        s.frames[0].strip() or "."
                        for s in (
                            spinner.Dot,
                            spinner.MiniDot,
                            spinner.Jump,
                            spinner.Line,
                            spinner.Pulse,
                            spinner.Points,
                            spinner.Meter,
                            spinner.Hamburger,
                        )
                    ),
                    Pen(fg=t.secondary),
                )
            ]
        ]
    )
    return join_vertical(
        LEFT,
        bubbles.dialog_title("Formats", width),
        Block.text(""),
        tags,
        Block.text(""),
        icons,
        spins,
        Block.text(""),
        bubbles.progress_bar(0.6, width),
        Block.text(""),
        bubbles.status(
            glyphs.PENDING,
            "Downloading",
            width,
            "Chillhop Essentials · Winter 2025",
            icon_color=t.success,
        ),
        bubbles.paginator_dots(1, 5),
        Block.text(""),
        bubbles.dialog(
            "Queue it?",
            "Chillhop Essentials · Winter 2025, 720p, about 410 MiB tonight.",
            width,
            keys=[("⏎", "queue"), ("esc", "back")],
        ),
        bubbles.wait_box("asking YouTube for the formats", 0, width),
    )


def gallery(width: int) -> Block:
    def framed(block: Block) -> Block:
        # A right edge in every line: if a glyph is drawn wider than one
        # column, its line's edge is pushed out and the eye catches it.
        edge = Block.from_rows(
            [[(" ", Pen()), ("│", Pen(fg=CHARM.separator))]] * block.height, 2
        )
        return join_horizontal(TOP, Style().width(width - 2).render(block), edge)

    sections = [
        ("Results", results_screen(width - 2)),
        ("Pieces", pieces(width - 2)),
        ("Borders", borders(width - 2)),
        ("charmtone", palette(width - 2)),
    ]
    parts: list[Block] = [
        bubbles.header("bewitch", [__version__], width),
        Block.text(""),
    ]
    for title, block in sections:
        parts += [bubbles.section(title, width), framed(block), Block.text("")]
    parts.append(
        Style()
        .foreground(CHARM.fg_most_subtle)
        .width(width)
        .align(CENTER)
        .render("every line should end at the same column")
    )
    return join_vertical(LEFT, *parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m bewitch", description=__doc__.split("\n")[0]
    )
    parser.add_argument(
        "--width",
        type=int,
        default=0,
        help="columns to draw at (default: this terminal's, 32-60)",
    )
    parser.add_argument(
        "--color",
        choices=sorted(_PROFILES),
        default=None,
        help="draw as this kind of terminal would (default: detect)",
    )
    args = parser.parse_args(argv)
    width = args.width or max(32, min(60, shutil.get_terminal_size((40, 24)).columns - 1))
    profile = _PROFILES[args.color] if args.color else detect()
    sys.stdout.write(ansi.render(gallery(width), profile) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
