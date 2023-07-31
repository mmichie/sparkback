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
}


def print_stats(data):
    print(f"Minimum: {min(data)}")
    print(f"Maximum: {max(data)}")
    print(f"Mean: {statistics.mean(data)}")
    print(f"Standard Deviation: {statistics.stdev(data)}")


def scale_data(data, ticks):
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
    print_ansi_spark(scale_data(args.numbers, ticks))

    if args.stats:
        print_stats(args.numbers)
