# -*- coding: utf-8 -*-
from __future__ import division
import argparse

TICKS_OPTIONS = {
    "default": ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"),
    "block": ("▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"),
    "ascii": (".", "o", "O", "#", "@"),
    "numeric": ("1", "2", "3", "4", "5"),
    "braille": ("⣀", "⣤", "⣶", "⣿"),
}


def scale_data(data, ticks):
    m = min(data)
    n = (max(data) - m) / (len(ticks) - 1)

    # if every element is the same height return all lower ticks, else compute
    # the tick height
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
    args = parser.parse_args()
    ticks = TICKS_OPTIONS[args.ticks]
    print_ansi_spark(scale_data(args.numbers, ticks))
