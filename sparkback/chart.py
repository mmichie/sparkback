# -*- coding: utf-8 -*-

"""
Multi-series time-series charts for the terminal.

render_chart() draws a chart in the style of a monitoring dashboard: a title with the
time range, a legend with per-series statistics, braille line plots over dotted
gridlines, a shared time axis, and a letter at the end of each line naming its series.

Series are ranked by magnitude (their largest absolute value) and only the largest are
drawn. Every panel's y-axis includes zero, so a series more than ten times smaller than
the largest series in its panel would be squashed against the baseline; such a series
starts a new panel with its own y-axis instead. All panels share the time axis.

The spark-chart command renders a chart from a JSON file or stdin:

    {
      "title": "db-cluster",
      "start": 1795388400,
      "end": 1795474800,
      "series": [
        {"name": "cpu", "points": [[1795388400, 4.54], [1795388430, null], [1795388460, 5.1]]}
      ]
    }

"title", "start" and "end" are optional. Times are unix seconds, shown in UTC; a null
value is a gap in the line.
"""

import argparse
import json
import math
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple

from .spark import ANSI_RESET, BrailleLineGraphStyle

# Series colors come from the terminal's 16-color palette, so they follow the user's theme.
# The order maximizes colorblind separation between neighboring series: under simulated
# protanopia and deuteranopia, every adjacent pair is at least 16 OKLab delta-E (x100)
# apart in the Tango and xterm palettes, against a usual minimum of 8. Each series also
# has a letter, so color is never the only way to tell series apart.
SERIES_COLORS = ("\033[36m", "\033[33m", "\033[31m", "\033[34m", "\033[32m", "\033[35m", "\033[96m", "\033[95m")
SERIES_LABELS = "abcdefgh"
MAX_SERIES = len(SERIES_COLORS)
MUTED = "\033[90m"  # axes, gridlines, and secondary text
BOLD = "\033[1m"

DEFAULT_HEIGHT = 12
MIN_PANEL_ROWS = 3
MIN_PLOT_WIDTH = 10
MIN_NAME_WIDTH = 8
NAME_WIDTH_WITH_TIMES = 20  # the legend drops the time of each maximum rather than cut names shorter
PANEL_SPLIT_RATIO = 10  # a series this many times smaller than its panel's largest starts a new panel
MIN_TICK_ROWS = 3  # preferred distance between y-axis ticks
X_LABEL_GAP = 3  # minimum blank columns between time labels
GRIDLINE = "┈"

DAY = 86400
WEEK = 7 * DAY
_TIME_STEPS = (1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, DAY, 2 * DAY, WEEK)
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_SI_PREFIXES = ((1e18, "E"), (1e15, "P"), (1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"))

Segment = Tuple[str, str]  # (text, ANSI style or "")


@dataclass
class Series:
    """
    A named time series.

    Attributes:
        name: The name shown in the legend.
        points: (time, value) pairs, with time in unix seconds. A value of None or NaN is a gap:
            the line is not drawn across it.
    """

    name: str
    points: Sequence[Tuple[float, Optional[float]]]


@dataclass
class _Line:
    """A series prepared for drawing: its points within the time range, and their statistics."""

    name: str
    points: List[Tuple[float, Optional[float]]]
    high: float
    high_time: float
    low: float
    mean: float
    last: float
    label: str = ""
    color: str = ""

    @property
    def magnitude(self) -> float:
        """The largest absolute value, used to rank series and to group them into panels."""
        return max(abs(self.high), abs(self.low))


class _Panel:
    """Series of similar magnitude sharing one y-axis."""

    def __init__(self, lines: List[_Line], rows: int) -> None:
        self.lines = lines
        self.rows = rows
        self.low = min(0.0, min(line.low for line in lines))
        self.high = max(0.0, max(line.high for line in lines))
        if self.high == self.low:  # every value is zero
            self.high = 1.0
        self.ticks: Dict[int, str] = {}
        for value in _y_ticks(self.low, self.high, rows):
            self.ticks.setdefault(self.y(value) // 4, format_value(value))
        self.ends: Dict[int, List[_Line]] = {}
        for line in lines:
            self.ends.setdefault(self.y(line.last) // 4, []).append(line)

    def y(self, value: float) -> int:
        """The braille pixel row for a value, counting from 0 at the top."""
        return round((self.high - value) / (self.high - self.low) * (4 * self.rows - 1))


def format_value(value: float) -> str:
    """
    Format a number to three significant figures: 22.7, 0.0202, 4.20, 105, 1.23k.

    A value that is exact at three significant figures prints without trailing zeros (16, 2.5, 0);
    a rounded one keeps them (4.20), so the digits shown always match the precision.

    Args:
        value: A finite number.

    Returns:
        The formatted number, with an SI suffix (k, M, G, T, P, E) from 1000 up.
    """
    rounded = float(f"{value:.3g}")
    if rounded == 0:
        return "0"
    exact = rounded == value
    suffix = ""
    for scale, prefix in _SI_PREFIXES:
        if abs(rounded) >= scale:
            rounded, suffix = rounded / scale, prefix
            break
    text = f"{rounded:.3g}" if exact else f"{rounded:#.3g}"
    return text.rstrip(".") + suffix


def render_chart(
    series: Sequence[Series],
    title: str = "",
    width: Optional[int] = None,
    height: int = DEFAULT_HEIGHT,
    start: Optional[float] = None,
    end: Optional[float] = None,
    max_series: int = MAX_SERIES,
    color: bool = True,
) -> str:
    """
    Render time series as a terminal chart with a legend, axes, and one panel per scale.

    Args:
        series: The series to chart, in any order; they are ranked by magnitude.
        title: Shown before the time range on the first line.
        width: Total width in columns (default: the terminal's width).
        height: Rows for the plot area, split evenly across panels; each panel gets at least 3.
        start: Start of the time range in unix seconds (default: the earliest point).
        end: End of the time range in unix seconds (default: the latest point). Points outside
            the range are ignored.
        max_series: How many of the largest series to draw, at most 8; a note counts the rest.
        color: Whether to emit ANSI color codes.

    Returns:
        The chart's lines joined by newlines, without a trailing newline.

    Raises:
        ValueError: If no series has a value in the time range, or a size argument is out of range.
    """
    if width is None:
        width = shutil.get_terminal_size().columns
    if height < MIN_PANEL_ROWS:
        raise ValueError(f"height must be at least {MIN_PANEL_ROWS}")
    if not 1 <= max_series <= MAX_SERIES:
        raise ValueError(f"max_series must be between 1 and {MAX_SERIES}")

    times = [time for item in series for time, _ in item.points]
    if start is None or end is None:
        if not times:
            raise ValueError("no data points to chart")
        start = min(times) if start is None else start
        end = max(times) if end is None else end
    if end < start:
        raise ValueError("end must not be before start")

    prepared = [_prepare(item, start, end) for item in series]
    ranked = sorted((line for line in prepared if line is not None), key=lambda line: -line.magnitude)
    if not ranked:
        raise ValueError("no data points to chart")
    shown = ranked[:max_series]
    for line, label, ansi in zip(shown, SERIES_LABELS, SERIES_COLORS):
        line.label, line.color = label, ansi

    output = _render(shown, title, width, height, start, end)
    if len(ranked) > len(shown):
        hidden = len(ranked) - len(shown)
        output.append([(f"{hidden} series not shown: these are the {len(shown)} largest of {len(ranked)}", MUTED)])
    if len(prepared) > len(ranked):
        output.append([(f"{len(prepared) - len(ranked)} series not shown: no data in this time range", MUTED)])
    return "\n".join(_join(segments, color) for segments in output)


def _render(lines: List[_Line], title: str, width: int, height: int, start: float, end: float) -> List[List[Segment]]:
    """Lay out the title, the legend and plot of each panel, and the time axis."""
    panels = _split_panels(lines, height)
    label_width = max(len(text) for panel in panels for text in panel.ticks.values())
    end_width = max(len(group) for panel in panels for group in panel.ends.values())
    plot_width = width - (label_width + 2) - (1 + end_width)
    if plot_width < MIN_PLOT_WIDTH:
        raise ValueError(f"width must be at least {width - plot_width + MIN_PLOT_WIDTH} for this chart")

    span = end - start if end > start else 1.0

    def x_of(time: float) -> int:
        return round((time - start) / span * (2 * plot_width - 1))

    seconds = any(time % 60 for time in (start, end)) or any(time % 60 for line in lines for time, _ in line.points)
    single_day = _utc(start).date() == _utc(end).date()

    def moment(time: float) -> str:
        clock = _clock(_utc(time), seconds)
        return clock if single_day else f"{_day(_utc(time))} {clock}"

    time_range = f"{_format_range(start, end, seconds)} UTC"
    output: List[List[Segment]] = []
    if title:
        title = _truncate_middle(_printable(title), max(MIN_NAME_WIDTH, width - len(time_range) - 3))
        output.append([(title, BOLD), (" · " + time_range, MUTED)])
    else:
        output.append([(time_range, MUTED)])

    legend = _legend(lines, width, moment)
    for panel in panels:
        output.extend(legend[line.label] for line in panel.lines)
        cells = _rasterize(panel, x_of, plot_width)
        output.extend(_plot_row(panel, row, cells[row], label_width) for row in range(panel.rows))
    output.extend(_time_axis(start, end, span, x_of, plot_width, label_width, end_width))
    return output


def _prepare(series: Series, start: float, end: float) -> Optional[_Line]:
    """Clip a series to [start, end] and compute its statistics; None if it has no values there."""
    points = sorted(
        (
            (time, value if value is not None and math.isfinite(value) else None)
            for time, value in series.points
            if start <= time <= end
        ),
        key=lambda point: point[0],
    )
    values = [(time, value) for time, value in points if value is not None]
    if not values:
        return None
    high_time, high = max(values, key=lambda point: point[1])  # the earliest time the maximum occurs
    return _Line(
        name=_printable(series.name),
        points=points,
        high=high,
        high_time=high_time,
        low=min(value for _, value in values),
        mean=math.fsum(value for _, value in values) / len(values),
        last=values[-1][1],
    )


def _split_panels(lines: List[_Line], height: int) -> List[_Panel]:
    """
    Group lines (largest first) into panels and share the rows out among them.

    A line joins the current panel unless it is more than PANEL_SPLIT_RATIO times smaller than the
    panel's first line. All-zero lines always join: they are flat at any scale.
    """
    groups: List[List[_Line]] = []
    for line in lines:
        if groups and (line.magnitude == 0 or line.magnitude * PANEL_SPLIT_RATIO >= groups[-1][0].magnitude):
            groups[-1].append(line)
        else:
            groups.append([line])
    rows, extra = divmod(max(height, MIN_PANEL_ROWS * len(groups)), len(groups))
    return [_Panel(group, rows + (1 if index < extra else 0)) for index, group in enumerate(groups)]


def _y_ticks(low: float, high: float, rows: int) -> List[float]:
    """
    Round-number ticks from low to high, a range that includes zero.

    The step is the smallest 1, 2, or 5 times a power of ten that puts ticks MIN_TICK_ROWS rows
    apart. When the panel is too short for that step to leave a tick besides zero, it is the largest
    such number that still does.
    """
    reach = max(high, -low)
    mantissa, exponent = _round_step((high - low) * 4 * MIN_TICK_ROWS / (4 * rows - 1), up=True)
    if _scaled(mantissa, exponent) > reach:
        mantissa, exponent = _round_step(reach, up=False)
    step = _scaled(mantissa, exponent)
    first = math.ceil(low / step - 1e-9)
    last = math.floor(high / step + 1e-9)
    return [_scaled(k * mantissa, exponent) for k in range(first, last + 1)]


def _round_step(target: float, up: bool) -> Tuple[int, int]:
    """The nearest number at or above (or below) target of the form m * 10**e with m in 1, 2, 5, as (m, e)."""
    exponent = math.floor(math.log10(target))
    candidates = [(m, e) for e in range(exponent - 1, exponent + 2) for m in (1, 2, 5)]
    if up:
        return min((c for c in candidates if _scaled(*c) >= target), key=lambda c: _scaled(*c))
    return max((c for c in candidates if _scaled(*c) <= target), key=lambda c: _scaled(*c))


def _scaled(mantissa: int, exponent: int) -> float:
    """mantissa * 10**exponent, divided rather than multiplied for negative exponents so 3e-1 is exactly 0.3."""
    return float(mantissa * 10**exponent) if exponent >= 0 else mantissa / 10**-exponent


def _legend(lines: List[_Line], width: int, moment: Callable[[float], str]) -> Dict[str, List[Segment]]:
    """
    Legend rows keyed by series label, with every column aligned across all panels.

    Long names are shortened to fit the width; if that would leave them fewer than NAME_WIDTH_WITH_TIMES
    columns, the time of each maximum is left out instead.
    """
    stats = {
        line.label: (
            format_value(line.high),
            moment(line.high_time),
            format_value(line.last),
            format_value(line.low),
            format_value(line.mean),
        )
        for line in lines
    }
    widths = [max(len(row[column]) for row in stats.values()) for column in range(5)]
    longest = max(len(line.name) for line in lines)
    room = width - (2 + len("  max ") + len(" at ") + len("  last ") + len("  min ") + len("  mean ") + sum(widths))
    show_times = room >= min(longest, NAME_WIDTH_WITH_TIMES)
    if not show_times:
        room += len(" at ") + widths[1]
    name_width = min(longest, max(MIN_NAME_WIDTH, room))
    rows = {}
    for line in lines:
        high, at, last, low, mean = stats[line.label]
        name = _truncate_middle(line.name, name_width)
        rows[line.label] = [
            (line.label, line.color),
            (" ", ""),
            (name, BOLD),
            (" " * (name_width - len(name)) + "  max ", MUTED),
            (high.rjust(widths[0]), line.color),
            ((" at " + at.ljust(widths[1]) if show_times else "") + "  last ", MUTED),
            (last.rjust(widths[2]), line.color),
            ("  min ", MUTED),
            (low.rjust(widths[3]), line.color),
            ("  mean ", MUTED),
            (mean.rjust(widths[4]), line.color),
        ]
    return rows


def _rasterize(panel: _Panel, x_of: Callable[[float], int], plot_width: int) -> List[List[Dict[int, int]]]:
    """The panel's braille cells, each mapping the index of every series with dots there to those dots' bits."""
    cells: List[List[Dict[int, int]]] = [[{} for _ in range(plot_width)] for _ in range(panel.rows)]
    for index, line in enumerate(panel.lines):
        for x, y in _pixels(line.points, x_of, panel.y):
            cell = cells[y // 4][x // 2]
            cell[index] = cell.get(index, 0) | BrailleLineGraphStyle.DOT_BITS[y % 4][x % 2]
    return cells


def _pixels(
    points: Sequence[Tuple[float, Optional[float]]], x_of: Callable[[float], int], y_of: Callable[[float], int]
) -> Iterator[Tuple[int, int]]:
    """Pixels of the line through the points, broken at gaps (None values)."""
    previous: Optional[Tuple[int, int]] = None
    for time, value in points:
        if value is None:
            previous = None
            continue
        current = (x_of(time), y_of(value))
        if previous is None:
            yield current
        else:
            yield from _segment(previous[0], previous[1], current[0], current[1])
        previous = current


def _segment(x0: int, y0: int, x1: int, y1: int) -> Iterator[Tuple[int, int]]:
    """Pixels on the straight line from (x0, y0) to (x1, y1), both ends included (Bresenham's algorithm)."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += step_x
        if doubled <= dx:
            error += dx
            y0 += step_y


def _plot_row(panel: _Panel, row: int, cells: List[Dict[int, int]], label_width: int) -> List[Segment]:
    """One row of a panel: the y-axis with its tick label, the plot, and the labels of lines ending here."""
    tick = panel.ticks.get(row)
    axis = "│" if tick is None else "┤"
    segments = [(f"{tick or '':>{label_width}} {axis}", MUTED)]
    for column, cell in enumerate(cells):
        if cell:
            # A cell has one color. Where series overlap, show each in turn across the columns, so none
            # disappears behind another and no dot is drawn in another series' color.
            owners = list(cell)
            owner = owners[column % len(owners)]
            segments.append((chr(BrailleLineGraphStyle.BRAILLE_BASE + cell[owner]), panel.lines[owner].color))
        elif tick is not None:
            segments.append((GRIDLINE, MUTED))
        else:
            segments.append((" ", ""))
    ending = panel.ends.get(row, [])
    if ending:
        segments.append((" ", ""))
        segments.extend((line.label, line.color) for line in ending)
    return segments


def _time_axis(
    start: float,
    end: float,
    span: float,
    x_of: Callable[[float], int],
    plot_width: int,
    label_width: int,
    end_width: int,
) -> List[List[Segment]]:
    """The x-axis rule with tick marks, and the time labels under it, each starting at its tick."""
    # The widest label is "23:59:59" for steps under a minute, otherwise "Nov 23".
    step = next(s for s in _time_steps() if s / span * plot_width >= (8 if s < 60 else 6) + X_LABEL_GAP)
    origin = 4 * DAY if step % WEEK == 0 else 0  # weekly ticks fall on Mondays, like 1970-01-05
    tick = origin + math.ceil((start - origin) / step) * step
    rule = ["─"] * plot_width
    labels = [" "] * (plot_width + 1 + end_width)
    free = 0  # the first column a label may start at
    while tick <= end:
        column = x_of(tick) // 2
        text = _tick_label(tick, step)
        stop = column + len(text)
        if column >= free and stop <= len(labels):
            rule[column] = "┬"
            labels[column:stop] = text
            free = stop + 1
        tick += step
    return [
        [(" " * label_width + " └" + "".join(rule), MUTED)],
        [(" " * (label_width + 2) + "".join(labels), MUTED)],
    ]


def _time_steps() -> Iterator[int]:
    """Candidate spacings between time ticks, in seconds, smallest first."""
    yield from _TIME_STEPS
    step = WEEK
    while True:
        step *= 2
        yield step


def _tick_label(time: float, step: int) -> str:
    """A time label: the date at midnight or for day-sized steps, otherwise the time of day."""
    moment = _utc(time)
    if step >= DAY or (moment.hour, moment.minute, moment.second) == (0, 0, 0):
        return _day(moment)
    return _clock(moment, step < 60)


def _format_range(start: float, end: float, seconds: bool) -> str:
    """The time range for the title, repeating only the parts of the end date that differ."""
    first, last = _utc(start), _utc(end)
    begin = f"{_day(first)} {first.year} {_clock(first, seconds)}"
    if last.date() == first.date():
        finish = _clock(last, seconds)
    elif last.year == first.year:
        finish = f"{_day(last)} {_clock(last, seconds)}"
    else:
        finish = f"{_day(last)} {last.year} {_clock(last, seconds)}"
    return f"{begin} → {finish}"


def _utc(time: float) -> datetime:
    return datetime.fromtimestamp(time, timezone.utc)


def _day(moment: datetime) -> str:
    return f"{_MONTHS[moment.month - 1]} {moment.day}"


def _clock(moment: datetime, seconds: bool) -> str:
    return moment.strftime("%H:%M:%S" if seconds else "%H:%M")


def _truncate_middle(text: str, width: int) -> str:
    """Shorten text to width characters by replacing its middle with an ellipsis."""
    if len(text) <= width:
        return text
    head = width // 2
    tail_start = len(text) - (width - 1 - head)
    return text[:head] + "…" + text[tail_start:]


def _printable(text: str) -> str:
    """Replace control and other non-printing characters, which would break the layout, with spaces."""
    return "".join(char if char.isprintable() else " " for char in text)


def _join(segments: Sequence[Segment], color: bool) -> str:
    """Render (text, style) segments as one line without trailing blanks, emitting each style change once."""
    segments = list(segments)
    while segments and not segments[-1][0].strip():
        segments.pop()
    if not segments:
        return ""
    segments[-1] = (segments[-1][0].rstrip(), segments[-1][1])
    if not color:
        return "".join(text for text, _ in segments)
    parts: List[str] = []
    current = ""
    for text, style in segments:
        if not style and not text.strip():
            style = current  # blanks look the same in any foreground color
        if style != current:
            parts.append((ANSI_RESET if current else "") + style)
            current = style
        parts.append(text)
    if current:
        parts.append(ANSI_RESET)
    return "".join(parts)


@dataclass
class ChartSpec:
    """A chart read from JSON: the arguments render_chart() takes from the data rather than the caller."""

    series: List[Series]
    title: str = ""
    start: Optional[float] = None
    end: Optional[float] = None


def parse_chart_spec(data: object) -> ChartSpec:
    """
    Validate a decoded JSON chart spec (see the module docstring for the format).

    Args:
        data: The decoded JSON.

    Returns:
        The chart's series, title, and time range.

    Raises:
        ValueError: If the spec is malformed or a timestamp is not plausible unix seconds.
    """
    if not (isinstance(data, dict) and isinstance(data.get("series"), list)):
        raise ValueError('expected a JSON object with a "series" list')
    title = data.get("title", "")
    if not isinstance(title, str):
        raise ValueError('"title" must be a string')
    start, end = data.get("start"), data.get("end")
    for key, value in (("start", start), ("end", end)):
        if value is not None and not _is_finite_number(value):
            raise ValueError(f'"{key}" must be a number of unix seconds')

    series = []
    for i, item in enumerate(data["series"]):
        if not (isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("points"), list)):
            raise ValueError(f'series[{i}]: expected an object with a "name" string and a "points" list')
        points = [_parse_point(point, f"series[{i}].points[{j}]") for j, point in enumerate(item["points"])]
        series.append(Series(item["name"], points))

    times = [time for item in series for time, _ in item.points]
    times.extend(value for value in (start, end) if value is not None)
    for time in (min(times), max(times)) if times else ():
        try:
            _utc(time)
        except (ValueError, OverflowError, OSError):
            raise ValueError(f"timestamp {time:.0f} is out of range: times must be unix seconds") from None
    return ChartSpec(series, title, start, end)


def _parse_point(point: object, where: str) -> Tuple[float, Optional[float]]:
    if not (
        isinstance(point, list)
        and len(point) == 2
        and _is_finite_number(point[0])
        and (point[1] is None or _is_number(point[1]))
    ):
        raise ValueError(f"{where}: expected [unix seconds, number or null]")
    return float(point[0]), None if point[1] is None else float(point[1])


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point for spark-chart: render a JSON chart spec from a file or stdin."""
    parser = argparse.ArgumentParser(
        prog="spark-chart",
        description="Render time series from a JSON chart spec as a terminal chart.",
    )
    parser.add_argument("file", nargs="?", default="-", help="the JSON chart spec, or - for stdin (default)")
    parser.add_argument("--width", type=int, help="width in columns (default: the terminal's width)")
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT, help=f"rows for the plot area (default: {DEFAULT_HEIGHT})"
    )
    parser.add_argument(
        "--max-series",
        type=int,
        default=MAX_SERIES,
        help=f"how many of the largest series to draw (default and maximum: {MAX_SERIES})",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="when to use color (default: auto, when writing to a terminal and NO_COLOR is unset)",
    )
    args = parser.parse_args(argv)

    if args.color == "auto":
        color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    else:
        color = args.color == "always"
    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        spec = parse_chart_spec(json.loads(text))
        chart = render_chart(
            spec.series,
            title=spec.title,
            width=args.width,
            height=args.height,
            start=spec.start,
            end=spec.end,
            max_series=args.max_series,
            color=color,
        )
    except (OSError, ValueError) as error:
        print(f"spark-chart: {error}", file=sys.stderr)
        return 1
    print(chart)
    return 0


if __name__ == "__main__":
    sys.exit(main())
