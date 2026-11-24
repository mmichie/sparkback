sparkback
=========

A Python library for generating sparklines in the terminal using Unicode characters.

## Installation

```bash
pip install sparkback
```

Or for development:

```bash
uv sync --all-extras
```

## Command Line Usage

Run sparkback with a series of numbers:

```bash
spark --ticks default 10 20 30 40 50
# ▁▃▅▆█
```

### Available Styles

```bash
spark --ticks default 10 20 30 40 50      # ▁▃▅▆█
spark --ticks block 10 20 30 40 50        # ▏▍▋▊█
spark --ticks ascii 10 20 30 40 50        # .oO#@
spark --ticks numeric 10 20 30 40 50      # 12345
spark --ticks braille 10 20 30 40 50      # ⣀⣤⣶⣶⣿
spark --ticks arrows 10 20 30 40 50       # →↑↑↑↑
spark --ticks line 10 20 30 40 50         # Multi-line box-drawing graph
spark --ticks multiline 10 20 30 40 50    # Multi-line bar chart
spark --ticks braille-line 10 20 30 40 50 # High-resolution braille line graph
```

### Color Support

Add color to any style with the `--color` flag:

```bash
# Value-based gradient (red -> yellow -> green)
spark --ticks default --color gradient 10 20 30 40 50 60 70 80 90 100

# Single color
spark --ticks braille-line --color cyan 1 5 3 8 2 6 4 7
spark --ticks default --color green 10 20 30 40 50
```

Available color schemes: `gradient`, `green`, `cyan`, `red`, `blue`, `magenta`, `yellow`

### Statistics

Use the `--stats` option to display statistics (the standard deviation is the sample standard deviation):

```bash
spark --ticks default 10 20 30 40 50 --stats
# Minimum: 10.0
# Maximum: 50.0
# Mean: 30.0
# Standard Deviation: 15.811388300841896
# ▁▃▅▆█
```

## Python API

```python
from sparkback.spark import get_style_instance, print_ansi_spark

# Basic usage
data = [10, 20, 30, 40, 50]
style = get_style_instance("default")
scaled = style.scale_data(data)
print_ansi_spark(scaled)

# High-resolution braille line graph
from sparkback.spark import BrailleLineGraphStyle, apply_color_to_output

data = [10, 45, 30, 80, 20, 60, 40, 70]
style = BrailleLineGraphStyle(height=3, filled=False)  # scaled to the data's min and max
graph = style.scale_data(data)

# On a fixed scale instead, such as 0-100 for percentages
percent_graph = BrailleLineGraphStyle(height=3, min_value=0, max_value=100).scale_data(data)

# Add color
colored = apply_color_to_output(graph, data, "gradient")
for row in colored:
    print("".join(row))
```

## Time-series charts

`spark-chart` draws several time series as one chart, like a monitoring dashboard. It shows a legend with
each series' max (and when it happened), last, min and mean; braille lines over gridlines; a shared time
axis; and a letter at the end of each line. Series are ranked by size and the eight largest are drawn. A
series more than ten times smaller than the largest in its panel gets its own panel and y-axis, so it is not
flattened against zero.

```bash
spark-chart metrics.json          # or pipe the JSON in: some-command | spark-chart
```

```
checkout-api · Nov 23 2026 12:00 → 13:00 UTC
a GET /cart        max  819 at 12:45  last   416  min   380  mean   484
b POST /checkout   max  200 at 12:08  last   178  min  54.5  mean   160
c GET /search      max  109 at 12:12  last   106  min  81.7  mean  97.0
    │                                            ⢰⠒⠒⠊⠉⠉⠒⠒⠊⠉⠑⢆
    │                                            ⡇          ⠘⡄
500 ┤⣀⣀⣀⣀⣀⡠⢄⣀⣀⠤⠤⢄⡠⠤⠤⣀⣀⣀⣀⣀⣀⣀⣀⣀┈┈⢀⡀┈┈┈┈┈┈┈┈┈┈┈⢀⡀┈┈⣰⠁┈┈┈┈┈┈┈┈┈┈┈⠱⠤⢄⣀⡠⠤⠤⣀⣀⣀⣀⡀┈┈⣀ a
    │                        ⠉⠉⠁⠈⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠁⠈⠉⠉                        ⠈⠉⠉
    │⠤⠤⠤⠤⠤⠔⠢⠤⠤⠒⠒⠢⠤⠔⠒⠤⠤⠤⠤⠤⠤⠤⠤ ⠠⠤⠤⠤⠤⣀⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⡀           ⡠⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤ b
  0 ┤⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠒⠉⠉⠑⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒⠑⠑⠒⠊⠒⠉⠒⠉⠒⠉⠒⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉ c
d p99 latency (s)  max 1.11 at 12:38  last 0.177  min 0.153  mean 0.328
  1 ┤┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈⢸⠉⠉⠉⠉⠉⠉⠉⠉⠉⠑⡆┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
    │                                            ⡎          ⢸
    │                                            ⡇          ⠘⡄
    │                                           ⢀⠇           ⡇
    │⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⡀ ⣀⣀       ⣀⡀ ⢀⣀⣀⣀⣀⣀⣀⣀⣀⣸            ⢸⣀⡀           ⣀ d
  0 ┤┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈⠈⠉┈┈⠉⠉⠉⠉⠉⠉⠉┈⠈⠉⠁┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈⠈⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉┈
    └┬───────────┬──────────┬───────────┬───────────┬───────────┬───────────
     12:00       12:10      12:20       12:30       12:40       12:50
```

In a terminal each series also gets its own color, from the terminal's 16-color palette in an order that
keeps neighboring series distinguishable for colorblind readers.

The input is JSON. Times are unix seconds, shown in UTC, and `null` is a gap in a line. `title`, `start`
and `end` are optional; the time range defaults to the span of the data.

```json
{
  "title": "checkout-api",
  "start": 1795435200,
  "end": 1795438800,
  "series": [
    {"name": "GET /cart", "points": [[1795435200, 421.5], [1795435260, 433.0], [1795435320, null]]},
    {"name": "POST /checkout", "points": [[1795435200, 180.2], [1795435260, 176.9]]}
  ]
}
```

Options: `--width` (default: the terminal's width), `--height` (rows for the plots, shared among panels;
default 12), `--max-series` (default and maximum 8), and `--color auto|always|never`.

From Python:

```python
from sparkback.chart import Series, render_chart

cart = Series("GET /cart", [(1795435200, 421.5), (1795435260, 433.0), (1795435320, 418.2)])
search = Series("GET /search", [(1795435200, 95.1), (1795435260, 99.4), (1795435320, 97.8)])
print(render_chart([cart, search], title="checkout-api", width=80))
```

## htop-style Demo

An example system monitor using braille graphs. It needs psutil, from the `demo` extra:

```bash
uv run --extra demo python examples/htop_demo.py
```

## See also

* https://github.com/holman/spark
* https://github.com/ajacksified/Clark/
