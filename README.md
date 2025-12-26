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
# ▁▂▄▆█
```

### Available Styles

```bash
spark --ticks default 10 20 30 40 50      # ▁▂▄▆█
spark --ticks block 10 20 30 40 50        # ▏▎▍▋█
spark --ticks ascii 10 20 30 40 50        # .oO#@
spark --ticks numeric 10 20 30 40 50      # 12345
spark --ticks braille 10 20 30 40 50      # ⣀⣤⣶⣿⣿
spark --ticks arrows 10 20 30 40 50       # →↗↗↗↗
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

Use the `--stats` option to display statistics:

```bash
spark --ticks default 10 20 30 40 50 --stats
# ▁▂▄▆█
# min: 10.00, max: 50.00, mean: 30.00, std: 14.14
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
style = BrailleLineGraphStyle(height=3, filled=False)
graph = style.scale_data(data)

# Add color
colored = apply_color_to_output(graph, data, "gradient")
for row in colored:
    print("".join(row))
```

## htop-style Demo

An example system monitor using braille graphs:

```bash
uv run python examples/htop_demo.py
```

## See also

* https://github.com/holman/spark
* https://github.com/ajacksified/Clark/
