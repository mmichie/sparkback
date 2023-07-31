# -*- coding: utf-8 -*-
from __future__ import division
import argparse
import statistics

TICKS_OPTIONS = {
    "default": ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"),
    "block": ("▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"),
    "ascii": (".", "o", "O", "#", "@"),
    "numeric": ("1", "2", "3", "4", "5"),
    "braille": ("⣀", "⣤", "⣶", "⣿"),
    "arrows": ("↓", "→", "↗", "↑"),
}


def print_stats(data):
    stats_str = (
        f"Minimum: {min(data)}\n"
        f"Maximum: {max(data)}\n"
        f"Mean: {statistics.mean(data)}\n"
        f"Standard Deviation: {statistics.stdev(data)}"
    )
    return stats_str


def scale_data(data, ticks, ticks_style):
    if ticks_style == "arrows":
        result = []
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                result.append(ticks[3])  # up arrow
            elif data[i] < data[i - 1]:
                result.append(ticks[0])  # down arrow
            else:
                result.append(ticks[1])  # right arrow for no change
        return result
    else:
        m = min(data)
        n = (max(data) - m) / (len(ticks) - 1)

        if n == 0:
            return (ticks[0] for t in data)
        else:
            return (ticks[int(round((t - m) / n))] for t in data)


def print_ansi_spark(d):
    print("".join(d))


def main():
    parser = argparse.ArgumentParser(description="Process numbers")
    parser.add_argument(
        "numbers", metavar="N", type=float, nargs="+", help="series of data to plot"
    )
    parser.add_argument(
        "--ticks",
        choices=TICKS_OPTIONS.keys(),
        default="default",
        help="the style of ticks to use",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="show statistics about the data",
    )
    args = parser.parse_args()
    ticks = TICKS_OPTIONS[args.ticks]
    print_ansi_spark(scale_data(args.numbers, TICKS_OPTIONS[args.ticks], args.ticks))

    if args.stats:
        print(print_stats(args.numbers))
