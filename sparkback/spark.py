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


class AbstractStyle:
    def scale_data(self, data, verbose=False):
        raise NotImplementedError


class ArrowsStyle(AbstractStyle):
    def __init__(self):
        self.ticks = ("↓", "→", "↗", "↑")

    def scale_data(self, data, verbose=False):
        result = []
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                result.append(self.ticks[3])  # up arrow
            elif data[i] < data[i - 1]:
                result.append(self.ticks[0])  # down arrow
            else:
                result.append(self.ticks[1])  # right arrow for no change
        return result


class DefaultStyle(AbstractStyle):
    def __init__(self, ticks):
        self.ticks = ticks

    def scale_data(self, data, verbose=False):
        min_data = min(data)
        range_data = (max(data) - min_data) / (len(self.ticks) - 1)
        if range_data == 0:
            return [self.ticks[0] for _ in data]
        else:
            scaled_data = [self.ticks[int(round((value - min_data) / range_data))] for value in data]
            if verbose:
                return [f"Data point {i} is {value}." for i, value in enumerate(scaled_data)]
            return scaled_data


STYLES = {
    "default": DefaultStyle,
    "block": DefaultStyle,
    "ascii": DefaultStyle,
    "numeric": DefaultStyle,
    "braille": DefaultStyle,
    "arrows": ArrowsStyle,
}


def print_ansi_spark(data_points, verbose=False):
    """
    Print the list of data points in the ANSI terminal.

    Args:
        d (list): A list of data points.
    """
    if verbose:
        print("\n".join(data_points))
    else:
        print("".join(data_points))


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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show verbose representation of the data",
    )

    args = parser.parse_args()
    style_instance = STYLES[args.ticks]()
    scaled_data = style_instance.scale_data(args.numbers)

    if args.verbose:
        for i, point in enumerate(args.numbers[1:], start=1):
            change_type = (
                "increased"
                if scaled_data[i] == style_instance.ticks[3]
                else "decreased"
                if scaled_data[i] == style_instance.ticks[0]
                else "remained the same"
            )
            print(f"Data point {i} has {change_type} from {args.numbers[i-1]} to {point}.")
    else:
        print_ansi_spark(scaled_data)

    if args.stats:
        print(print_stats(args.numbers))
