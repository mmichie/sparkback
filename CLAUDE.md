# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sparkback is a Python library for generating sparklines in the terminal using various Unicode characters. It provides both a command-line tool and a Python API for visualizing numerical data as compact inline graphs, plus multi-series time-series charts with legends and axes (`spark-chart`).

## Development Setup

```bash
uv sync --all-extras
```

## Common Commands

### Running the CLI
```bash
# Using uv run
uv run spark --ticks default 10 20 30 40 50

# Or directly via bin/spark
bin/spark --ticks default 10 20 30 40 50

# Time-series chart from a JSON spec (file or stdin)
uv run spark-chart chart.json --width 100
```

### Testing
```bash
# Run all tests
uv run pytest

# Run a specific test
uv run pytest tests/spark_test.py::test_scale_data_default
```

### Linting and Formatting
```bash
# Format code with Black
uv run black .

# Run linters (all configured for 120 character line length)
uv run flake8 .
uv run pylint --recursive=y sparkback tests examples
```

CI (.github/workflows/python.yml) fails on `black --check .`, any flake8 finding, and pylint errors or warnings (`--disable=C,R`; the convention and refactor messages are advice), and runs the tests on Python 3.11 and 3.15. It installs with `uv sync --locked`, so run `uv lock` after changing dependencies.

### Building
```bash
uv build
```

## Architecture

The codebase is structured around a simple object-oriented design pattern:

### Core Components

1. **AbstractStyle Base Class** (sparkback/spark.py)
   - Defines the interface for all visualization styles (an `abc.ABC`)
   - Single abstract method: `scale_data(data, verbose=False)`

2. **Style Implementations**
   All style classes inherit from AbstractStyle and implement the `scale_data` method:
   - **DefaultStyle**: Unicode blocks (▁▂▃▄▅▆▇█) - scales linearly to data range
   - **BlockStyle**: Alternative blocks (▏▎▍▌▋▊▉█) - inherits DefaultStyle's scaling
   - **AsciiStyle**: ASCII characters (.oO#@) - inherits DefaultStyle's scaling
   - **NumericStyle**: Numbers (1-5) - inherits DefaultStyle's scaling
   - **BrailleStyle**: Braille characters (⣀⣤⣶⣿) - inherits DefaultStyle's scaling
   - **ArrowsStyle**: Directional indicators (↓→↗↑) - shows trend between consecutive values
   - **MultiLineGraphStyle**: Vertical bar chart rendered across 10 lines
   - **LineGraphStyle**: Connected line graphs using box-drawing characters (─│╱╲●) - configurable height
   - **BrailleLineGraphStyle**: High-resolution line graphs in braille, two data points per character - configurable height, optional fill

3. **Key Functions**
   - `get_style_instance(style)`: Factory function returning style instances from the STYLES dict
   - `print_ansi_spark(data_points, verbose)`: Renders sparklines (handles both single-line and multi-line output)
   - `print_stats(data)`: Computes min, max, mean, and standard deviation

### Data Flow

1. CLI arguments parsed via `get_args()` → returns argparse.Namespace
2. Style instance created via `get_style_instance(args.ticks)` → returns AbstractStyle subclass
3. Data scaled via `style_instance.scale_data(args.numbers)` → returns list of characters or 2D grid
4. Output via `print_ansi_spark(scaled_data)` → prints to terminal

### Time-series Charts (sparkback/chart.py)

`render_chart(series, ...)` draws `Series(name, points)` (points are `(unix_seconds, value_or_None)`) as a multi-panel chart: title with the UTC time range, aligned legend (max with its time, last, min, mean), braille plots over `┈` gridlines, a shared time axis, and series letters at line ends. `spark-chart` (`main`) reads a JSON spec validated by `parse_chart_spec`.

1. `_prepare` clips each series to [start, end] and computes its stats; series without values are dropped and noted
2. Series are ranked by magnitude (max |value|); the largest `max_series` (at most 8, one per color) get letters a-h
3. `_split_panels` starts a new panel when a series is more than 10x smaller than its panel's largest; every y-axis includes zero
4. `_rasterize` draws each series with Bresenham lines into 2x4-dot braille cells; `_plot_row` alternates between series that share a cell, so none is hidden
5. Output is built as `(text, ANSI style)` segments and joined by `_join`, which drops trailing blanks and redundant escape codes

Series colors are ANSI 16-color codes (theme-adaptive) in an order chosen for colorblind separation between adjacent series; keep that order when changing the palette.

### Adding a New Style

To add a new visualization style:
1. Create a class inheriting from AbstractStyle
2. Define the `scale_data(data, verbose)` method
3. Add the class to the STYLES dictionary in sparkback/spark.py
4. The new style will automatically appear in CLI `--ticks` choices
5. Export it from sparkback/__init__.py, which lists the public API explicitly (imports and `__all__`)

## Code Standards

- Line length: 120 characters (enforced by Black, flake8, pylint)
- Python version: >=3.11 (the oldest maintained release; CI tests 3.11 and the newest)
- Test files use: `# flake8: noqa` and `# pylint: skip-file`
