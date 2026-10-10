"""The parts of a Charm screen: Bubbles' drawing, and Crush's chrome.

Named after Charm's Bubbles, which this follows for the spinners, the help
line, the progress bar and the paginator. Unlike Bubbles these are drawing
recipes, not components: they hold no state and read no keys, because the
app — and whatever TUI library it runs on — owns those. Each takes the
state it should draw and a width, and returns a
:class:`~bewitch.lipgloss.Block` exactly that wide.

:mod:`bewitch.bubbles.crush` holds the pieces Bubbles does not have but
Crush's screens are built from: the header band, section rules, dialog
titles, labels and status rows.
"""

from bewitch.bubbles import spinner
from bewitch.bubbles.crush import (
    dialog,
    dialog_title,
    header,
    section,
    status,
    tag,
    wait_box,
)
from bewitch.bubbles.spinner import Spinner
from bewitch.bubbles.widgets import (
    list_item,
    paginator_dots,
    progress_bar,
    scroll_thumb,
    scrollbar,
    short_help,
)

__all__ = [
    "Spinner",
    "dialog",
    "dialog_title",
    "header",
    "list_item",
    "paginator_dots",
    "progress_bar",
    "scroll_thumb",
    "scrollbar",
    "section",
    "short_help",
    "spinner",
    "status",
    "tag",
    "wait_box",
]
