# Third-party notices

bewitch ports, into Python, the behaviour and API of these MIT-licensed
libraries by Charmbracelet, Inc.:

| Library | Version followed | What bewitch takes from it |
|---|---|---|
| [Lip Gloss](https://github.com/charmbracelet/lipgloss) | v2.0.6 | `Style` and its render order, the border sets, joins and placement, `Blend1D` |
| [charmtone](https://github.com/charmbracelet/x/tree/main/exp/charmtone) (in `charmbracelet/x`) | v0.1.0 | the palette: names, values, order and groups |
| [Bubbles](https://github.com/charmbracelet/bubbles) | v2.2.1 | spinner frames and rates, the short help layout, the progress bar's blend, the paginator's dots |
| [huh](https://github.com/charmbracelet/huh) | v2.0.3 | how the Charm theme marks an option: `✓` ticked, `•` not (the look only; no code) |
| [colorprofile](https://github.com/charmbracelet/colorprofile) | v0.4.3 | colour detection from the environment |
| [x/ansi](https://github.com/charmbracelet/x/tree/main/ansi) (in `charmbracelet/x`) | v0.11.9 | 256-colour conversion, which x/ansi in turn ports from tmux's `colour.c` |

Their licence, which applies to the parts of bewitch derived from them. The
copyright lines are each repository's own:

```
Lip Gloss:     Copyright (c) 2021-2026 Charmbracelet, Inc.
Bubbles:       Copyright (c) 2020-2026 Charmbracelet, Inc.
huh:           Copyright (c) 2023–2026 Charm
colorprofile:  Copyright (c) 2020-2024 Charmbracelet, Inc
charmtone, x/ansi (charmbracelet/x):
               Copyright (c) 2023 Charmbracelet, Inc.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Crush

The look `bewitch.bubbles.crush` and `bewitch.theme` reproduce — the `╱` header
band, section rules, filled selection bars, which charmtone each colour role is
drawn in — is taken from how [Crush](https://github.com/charmbracelet/crush)
looks. Crush is licensed under FSL-1.1-MIT, not MIT, so **no Crush code is
copied here**: those modules are written from the design, and anything that
needed code was ported from the MIT libraries above instead.

"Charm", "Lip Gloss", "Bubbles", "Bubble Tea", "huh" and "Crush" are Charm's names
for Charm's products. bewitch uses them to say whose work it ports, and is not
affiliated with or endorsed by Charm.
