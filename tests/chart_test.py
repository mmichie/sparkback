# flake8: noqa
# pylint: skip-file
# mypy: ignore-errors

import calendar
import io
import json
import re

import pytest

import sparkback.chart as chart
from sparkback.chart import Series, format_value, parse_chart_spec, render_chart

ANSI = re.compile(r"\033\[[0-9;]*m")
NOON = calendar.timegm((2026, 11, 23, 12, 0, 0))
MINUTES = [NOON + 60 * i for i in range(10)]


def fixture_series():
    return [
        Series("errors", list(zip(MINUTES, [1, 1, 2, 1, 3, 2, 4, 3, 5, 6]))),
        Series("requests", list(zip(MINUTES, [10, 12, 15, 11, 18, 25, 22, 30, 28, 40]))),
        Series("latency p99", list(zip(MINUTES, [0.2, 0.25, 0.22, 0.3, 0.28, 0.35, 0.3, 0.4, 0.38, 0.45]))),
    ]


def flat(name, value, times=MINUTES):
    return Series(name, [(t, value) for t in times])


def utc(*fields):
    return calendar.timegm(fields + (0,) * (6 - len(fields)))


# Checked by hand: requests and errors share a panel (6 is within 10x of 40), latency gets its own;
# ticks sit on round numbers; time ticks are 2 minutes apart, each label starting at its tick.
GOLDEN = """\
api · Nov 23 2026 12:00 → 12:09 UTC
a requests     max   40 at 12:09  last   40  min  10  mean  21.1
b errors       max    6 at 12:09  last    6  min   1  mean   2.8
 40 ┤┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈⣀⡠⠤⠔⠒⠉ a
    │                           ⣀⣀⣀⠤⠤⠤⠤⢄⣀⣀⣀⣀⠤⠤⠒⠒⠉⠉⠉⠉⠉⠉⠉⠉
 20 ┤⣀⣀⣀⡠⠤⠤⠤⠤⠤⠔⠒⠒⠒⠒⠢⠤⠤⢄⣀⣀⠤⠤⠒⠒⠉⠉⠉┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
  0 ┤⣀⣀⣀⣀⣀⣀⣀⣀⣀⡠⠤⠤⠤⠤⠤⠤⣀⣀⣀⣀⣀⣀⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠒⠒⠒⠒⠒⠒⠒⠒⠒⠒ b
c latency p99  max 0.45 at 12:09  last 0.45  min 0.2  mean 0.313
0.4 ┤┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈⢀⣀⣀┈┈┈┈┈┈┈┈⣀⣀⠤⠤⠤⠤⠤⠤⠤⠤⠤⠒⠒⠒⠉⠉ c
    │   ⢀⣀⣀⣀⣀⣀⡀    ⣀⣀⠤⠤⠒⠒⠒⠒⠤⠤⠤⠤⠔⠒⠊⠉⠁  ⠉⠉⠉⠒⠒⠒⠉⠉
0.2 ┤⠉⠉⠉⠁┈┈┈┈┈⠈⠉⠉⠉⠉┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
  0 ┤┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
    └┬───────────┬────────────┬───────────┬────────────┬──────
     12:00       12:02        12:04       12:06        12:08"""


def test_golden_chart():
    assert render_chart(fixture_series(), title="api", width=64, height=8, color=False) == GOLDEN


def test_color_only_adds_escape_codes():
    colored = render_chart(fixture_series(), title="api", width=64, height=8, color=True)
    assert ANSI.sub("", colored) == GOLDEN


def test_colors_follow_series_and_chrome_is_muted():
    lines = render_chart(fixture_series(), title="api", width=64, height=8).split("\n")
    cyan, yellow = chart.SERIES_COLORS[:2]
    assert lines[0].startswith(chart.BOLD + "api")
    assert lines[1].startswith(cyan + "a")
    assert lines[2].startswith(yellow + "b")
    assert chart.MUTED + " 40 ┤┈" in lines[3]
    assert re.search(re.escape(cyan) + "[^\033]* a" + re.escape(chart.ANSI_RESET) + "$", lines[3])  # end label
    assert yellow + "⣀" in lines[6]


@pytest.mark.parametrize(
    "value, expected",
    [
        (22.68, "22.7"),
        (4.1987, "4.20"),
        (0.020213, "0.0202"),
        (105.2, "105"),
        (16, "16"),
        (2.5, "2.5"),
        (0, "0"),
        (-0.0, "0"),
        (1, "1"),
        (0.74712, "0.747"),
        (1234, "1.23k"),
        (1500, "1.5k"),
        (999.95, "1.00k"),
        (2.5e9, "2.5G"),
        (-4.1987, "-4.20"),
        (-1500, "-1.5k"),
        (0.3, "0.3"),
    ],
)
def test_format_value(value, expected):
    assert format_value(value) == expected


@pytest.mark.parametrize(
    "low, high, rows, expected",
    [
        (0, 22.7, 6, [0, 20]),
        (0, 105, 5, [0, 100]),
        (0, 9.09, 6, [0, 5]),
        (0, 1.14, 7, [0, 1]),
        (0, 0.7, 12, [0, 0.2, 0.4, 0.6]),
        (-10, 10, 6, [-10, 0, 10]),
        (-3, 0, 6, [-2, 0]),
        (0, 9.09, 3, [0, 5]),  # too short for 3-row spacing: still a tick besides zero
    ],
)
def test_y_ticks(low, high, rows, expected):
    assert chart._y_ticks(low, high, rows) == expected


def test_y_tick_values_are_exact_decimals():
    assert [format_value(t) for t in chart._y_ticks(0, 0.7, 12)] == ["0", "0.2", "0.4", "0.6"]


def test_segment_is_bresenham():
    assert list(chart._segment(0, 0, 3, 1)) == [(0, 0), (1, 0), (2, 1), (3, 1)]
    assert list(chart._segment(2, 3, 2, 0)) == [(2, 3), (2, 2), (2, 1), (2, 0)]


def test_gaps_break_the_line():
    points = [(0, 1.0), (1, None), (2, 1.0), (3, 1.0)]
    pixels = list(chart._pixels(points, lambda t: int(t) * 4, lambda _: 0))
    assert (4, 0) not in pixels and (2, 0) not in pixels  # nothing drawn across the gap
    assert pixels[0] == (0, 0) and (8, 0) in pixels and (12, 0) in pixels


def time_labels(output):
    return output.split("\n")[-1].split()


def test_time_axis_over_a_day_marks_midnight_with_the_date():
    times = range(utc(2026, 11, 22, 23), utc(2026, 11, 23, 21, 38, 30) + 1, 30)
    output = render_chart([Series("cpu", [(t, 1.0) for t in times])], width=180, color=False)
    labels = time_labels(output)
    assert labels[:3] == ["Nov", "23", "02:00"]
    assert labels[-1] == "20:00"


def test_time_axis_over_two_hours_uses_ten_minute_steps():
    times = range(utc(2026, 11, 23, 20, 58), utc(2026, 11, 23, 22, 54) + 1, 60)
    output = render_chart([Series("cpu", [(t, 1.0) for t in times])], width=180, color=False)
    assert time_labels(output) == [f"{h}:{m}0" for h in (21, 22) for m in range(6)]


def test_time_axis_with_seconds():
    times = range(NOON, NOON + 60, 1)
    output = render_chart([Series("cpu", [(t, 1.0) for t in times])], width=80, color=False)
    assert time_labels(output)[:2] == ["12:00:00", "12:00:10"]


def test_title_range_across_days_with_seconds():
    series = [flat("cpu", 1.0, [utc(2026, 11, 22, 23), utc(2026, 11, 23, 21, 38, 30)])]
    title = render_chart(series, title="cluster", width=100, color=False).split("\n")[0]
    assert title == "cluster · Nov 22 2026 23:00:00 → Nov 23 21:38:30 UTC"


def test_title_range_within_a_day():
    series = [flat("cpu", 1.0, [utc(2026, 11, 23, 20, 58), utc(2026, 11, 23, 22, 54)])]
    assert render_chart(series, width=100, color=False).split("\n")[0] == "Nov 23 2026 20:58 → 22:54 UTC"


def test_title_range_across_years():
    series = [flat("cpu", 1.0, [utc(2026, 12, 31, 22), utc(2027, 1, 1, 2)])]
    assert render_chart(series, width=100, color=False).split("\n")[0] == "Dec 31 2026 22:00 → Jan 1 2027 02:00 UTC"


def test_time_of_maximum_includes_the_date_across_days():
    series = [
        Series("cpu", [(utc(2026, 11, 22, 23), 1.0), (utc(2026, 11, 23, 6, 9), 6.53), (utc(2026, 11, 23, 9), 2.0)])
    ]
    legend = render_chart(series, width=100, color=False).split("\n")[1]
    assert "max 6.53 at Nov 23 06:09  last 2" in legend


def test_maximum_reports_its_first_occurrence():
    series = [Series("acu", list(zip(MINUTES, [2.5, 16, 16, 16, 4, 16, 16, 16, 16, 16])))]
    assert "max 16 at 12:01" in render_chart(series, width=100, color=False)


def legend_rows(output):
    return [line for line in output.split("\n") if re.match(r"[a-h] ", line)]


def test_series_are_ranked_and_split_into_panels_by_scale():
    # Maxima from the reference chart: g is within 10x of a and stays; h is not and gets its own panel.
    maxima = [2.41, 22.7, 1.14, 13.3, 7.43, 6.53, 4.53, 4.20]
    series = [flat(f"s{m}", m) for m in maxima]
    output = render_chart(series, width=120, height=12, color=False)
    lines = output.split("\n")
    assert [row.split()[1] for row in legend_rows(output)] == [f"s{m}" for m in sorted(maxima, reverse=True)]
    h_row = next(i for i, line in enumerate(lines) if line.startswith("h "))
    g_row = next(i for i, line in enumerate(lines) if line.startswith("g "))
    assert h_row - g_row == 7  # g's legend row, then the 6 plot rows of the first panel
    assert sum(1 for line in lines if "└" in line) == 1  # one shared time axis


def test_series_beyond_the_limit_are_counted():
    series = [flat(f"s{i}", float(i)) for i in range(1, 13)]
    output = render_chart(series, width=100, color=False)
    assert output.split("\n")[-1] == "4 series not shown: these are the 8 largest of 12"
    assert [row[0] for row in legend_rows(output)] == list("abcdefgh")
    assert "s12" in output and "s4 " not in output and "s1 " not in output


def test_max_series_limits_the_chart():
    series = [flat(f"s{i}", float(i + 1)) for i in range(4)]
    output = render_chart(series, width=100, max_series=2, color=False)
    assert len(legend_rows(output)) == 2
    assert output.endswith("2 series not shown: these are the 2 largest of 4")


def test_series_without_data_are_noted():
    series = [flat("cpu", 1.0), Series("empty", [(MINUTES[0], None), (MINUTES[1], float("nan"))])]
    output = render_chart(series, width=100, color=False)
    assert output.endswith("1 series not shown: no data in this time range")
    assert "empty" not in output


def test_lines_ending_on_the_same_row_share_one_label_cell():
    series = [flat("one", 10.0), flat("two", 9.9), flat("three", 1.0)]
    rows = render_chart(series, width=60, height=6, color=False).split("\n")
    assert any(row.endswith(" ab") for row in rows)
    assert any(row.endswith(" c") for row in rows)


def test_overlapping_series_alternate_cells():
    series = [flat("one", 5.0), flat("two", 5.0)]
    output = render_chart(series, width=40, height=4)
    row = next(line for line in output.split("\n") if ANSI.sub("", line).endswith(" ab"))
    first, second = chart.SERIES_COLORS[:2]
    plot = row[row.index("┤") :]
    assert plot.count(first) > 5 and plot.count(second) > 5  # both stay visible


def test_negative_values():
    series = [Series("delta", list(zip(MINUTES, [-8, -4, 0, 4, 2, -2, -6, 1, 3, 5])))]
    output = render_chart(series, width=60, height=6, color=False)
    assert "min -8" in output
    tick_labels = [line.split("┤")[0].strip() for line in output.split("\n") if "┤" in line]
    assert tick_labels == ["5", "0", "-5"]


def test_all_zero_series():
    output = render_chart([flat("idle", 0.0), flat("cpu", 3.0)], width=60, height=6, color=False)
    assert "a cpu" in output and "b idle" in output
    assert sum(1 for line in output.split("\n") if line.startswith(("a ", "b "))) == 2
    assert render_chart([flat("idle", 0.0)], width=60, color=False)


def test_single_point():
    output = render_chart([Series("once", [(NOON, 3.0)])], width=60, color=False)
    assert output.split("\n")[0] == "Nov 23 2026 12:00 → 12:00 UTC"
    assert "max 3 at 12:00" in output


def test_points_are_sorted_and_clipped_to_the_range():
    points = [(MINUTES[5], 50.0), (MINUTES[1], 1.0), (MINUTES[9], 99.0), (MINUTES[3], 3.0)]
    output = render_chart([Series("cpu", points)], width=100, start=MINUTES[0], end=MINUTES[6], color=False)
    assert output.split("\n")[0] == "Nov 23 2026 12:00 → 12:06 UTC"
    assert "max 50 at 12:05  last 50  min 1  mean 18" in output


def test_names_are_shortened_and_times_dropped_to_fit():
    long_name = "avg:aws.rds.cpuutilization dbinstanceidentifier:staging-api-aurora-instance-0"
    times = [utc(2026, 11, 22, 23), utc(2026, 11, 23, 21, 38, 30)]
    series = [
        Series(long_name, list(zip(times, [4.54, 22.7]))),
        Series(long_name[:-1] + "1", list(zip(times, [3, 6.5]))),
    ]
    for width in (56, 64, 80, 90, 100, 180):
        lines = render_chart(series, width=width, color=False).split("\n")
        assert max(len(line) for line in lines) <= width
        assert len({line.index("max") for line in legend_rows("\n".join(lines))}) == 1  # aligned
    narrow, wide = (legend_rows(render_chart(series, width=w, color=False))[0] for w in (80, 100))
    assert (
        " at " not in narrow
        and "…" in narrow
        and narrow.endswith("instance-0  max 22.7  last 22.7  min 4.54  mean 13.6")
    )
    assert "max 22.7 at Nov 23 21:38:30" in wide and "…" in wide


def test_control_characters_in_names_are_replaced():
    output = render_chart([flat("bad\x1b[31mname\nhere", 1.0)], title="t\x07itle", width=80, color=False)
    assert "\x1b" not in output and "\x07" not in output
    assert "bad [31mname here" in output and output.startswith("t itle · ")


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"height": 2}, "height must be at least 3"),
        ({"max_series": 9}, "max_series must be between 1 and 8"),
        ({"max_series": 0}, "max_series must be between 1 and 8"),
        ({"width": 12}, "width must be at least 17 for this chart"),
        ({"start": MINUTES[5], "end": MINUTES[1]}, "end must not be before start"),
        ({"start": MINUTES[9] + 60, "end": MINUTES[9] + 120}, "no data points to chart"),
    ],
)
def test_invalid_arguments(kwargs, message):
    with pytest.raises(ValueError, match=message):
        render_chart(fixture_series(), **{"width": 80, **kwargs})


def test_no_series():
    with pytest.raises(ValueError, match="no data points to chart"):
        render_chart([], width=80)


def test_options_are_keyword_only():
    with pytest.raises(TypeError):
        render_chart(fixture_series(), "api", 64)  # type: ignore[misc]


def test_parse_chart_spec():
    spec = parse_chart_spec(
        {
            "title": "db",
            "start": 10,
            "end": 20.5,
            "series": [{"name": "cpu", "points": [[10, 1], [15, None], [20, 2.5]]}],
        }
    )
    assert spec.title == "db" and spec.start == 10 and spec.end == 20.5
    assert spec.series == [Series("cpu", [(10.0, 1.0), (15.0, None), (20.0, 2.5)])]
    assert parse_chart_spec({"series": []}).title == ""


@pytest.mark.parametrize(
    "data, message",
    [
        ([], 'expected a JSON object with a "series" list'),
        ({"series": {}}, 'expected a JSON object with a "series" list'),
        ({"series": [], "title": 3}, '"title" must be a string'),
        ({"series": [], "start": "noon"}, '"start" must be a number of unix seconds'),
        ({"series": [{"name": "cpu"}]}, r'series\[0\]: expected an object with a "name" string and a "points" list'),
        ({"series": [{"name": "cpu", "points": [[1, 2, 3]]}]}, r"series\[0\]\.points\[0\]: expected"),
        ({"series": [{"name": "cpu", "points": [[True, 2]]}]}, r"series\[0\]\.points\[0\]: expected"),
        ({"series": [{"name": "cpu", "points": [[1, "2"]]}]}, r"series\[0\]\.points\[0\]: expected"),
        ({"series": [{"name": "cpu", "points": [[1763852400000, 2]]}]}, "times must be unix seconds"),
    ],
)
def test_parse_chart_spec_rejects(data, message):
    with pytest.raises(ValueError, match=message):
        parse_chart_spec(data)


def test_cli_renders_a_file(tmp_path, capsys):
    spec = {
        "title": "api",
        "series": [{"name": s.name, "points": [list(p) for p in s.points]} for s in fixture_series()],
    }
    path = tmp_path / "chart.json"
    path.write_text(json.dumps(spec))
    assert chart.main([str(path), "--width", "64", "--height", "8", "--color", "never"]) == 0
    assert capsys.readouterr().out == GOLDEN + "\n"


def test_cli_reads_stdin_and_colors_on_request(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"series": [{"name": "cpu", "points": [[0, 1], [60, 2]]}]}))
    )
    assert chart.main(["--width", "60", "--color", "always"]) == 0
    assert chart.SERIES_COLORS[0] in capsys.readouterr().out


def test_cli_auto_color_is_off_when_not_a_terminal(tmp_path, capsys):
    path = tmp_path / "chart.json"
    path.write_text(json.dumps({"series": [{"name": "cpu", "points": [[0, 1], [60, 2]]}]}))
    assert chart.main([str(path), "--width", "60"]) == 0
    assert "\033[" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "content, message",
    [
        ("{not json", "spark-chart: Expecting property name"),
        ('{"series": 1}', 'spark-chart: expected a JSON object with a "series" list'),
        ('{"series": []}', "spark-chart: no data points to chart"),
    ],
)
def test_cli_reports_bad_input(tmp_path, capsys, content, message):
    path = tmp_path / "chart.json"
    path.write_text(content)
    assert chart.main([str(path), "--width", "80"]) == 1
    assert capsys.readouterr().err.startswith(message)


def test_cli_reports_a_missing_file(tmp_path, capsys):
    assert chart.main([str(tmp_path / "missing.json")]) == 1
    assert "No such file or directory" in capsys.readouterr().err
