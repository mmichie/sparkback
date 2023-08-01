# -*- coding: utf-8 -*-

"""
This module provides functionalities to visualize numerical data in the terminal.

It includes different styles of visualization represented by the TICKS_OPTIONS dictionary. 
Data can be represented in default, block, ascii, numeric, braille, and arrows styles.

The module can also compute and print basic statistics about the data if required.

Functions included are:
- print_stats: Compute and format basic statistics from the given data.
- scale_data: Scale the data according to the selected ticks style.
- print_ansi_spark: Print the list of data points in the ANSI terminal.
- main: Main function that parses command line arguments and calls the corresponding functions.

Example usage:

    python3 this_file.py 1.0 2.5 3.3 4.7 3.5 --ticks="block" --stats
"""

from __future__ import division

import argparse
import statistics

# Dictionary of available options for data visualization
TICKS_OPTIONS = {
    "default": ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"),
    "block": ("▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"),
    "ascii": (".", "o", "O", "#", "@"),
    "numeric": ("1", "2", "3", "4", "5"),
    "braille": ("⣀", "⣤", "⣶", "⣿"),
    "arrows": ("↓", "→", "↗", "↑"),
}


def print_stats(data):
    """
    Compute and format basic statistics from the given data.

    Args:
        data (list): A list of numerical data.

    Returns:
        str: A string of formatted statistics.
    """
    stats_str = (
        f"Minimum: {min(data)}\n"
        f"Maximum: {max(data)}\n"
        f"Mean: {statistics.mean(data)}\n"
        f"Standard Deviation: {statistics.stdev(data)}"
    )
    return stats_str


def scale_data(data, ticks, ticks_style):
    """
    Scale the data according to the selected ticks style.

    Args:
        data (list): A list of numerical data.
        ticks (tuple): A tuple of characters representing the ticks.
        ticks_style (str): A string representing the style of ticks to use.

    Returns:
        list: A list of ticks representing the scaled data.
    """
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
    """
    Print the list of data points in the ANSI terminal.

    Args:
        d (list): A list of data points.
    """
    print("".join(d))


def main():
    """
    Main function that parses command line arguments and calls the corresponding functions.
    """
    parser = argparse.ArgumentParser(description="Process numbers")
    parser.add_argument("numbers", metavar="N", type=float, nargs="+", help="series of data to plot")
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
    TICKS_OPTIONS[args.ticks]
    print_ansi_spark(scale_data(args.numbers, TICKS_OPTIONS[args.ticks], args.ticks))

    if args.stats:
        print(print_stats(args.numbers))
        print(print_stats(args.numbers))
