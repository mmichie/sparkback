# -*- coding: utf-8 -*-

"""
This module provides functionalities to visualize numerical data in the terminal.

It includes different styles of visualization, data can be represented in
default, block, ascii, numeric, braille, and arrows styles.

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


def print_stats(data):
    """
    Compute and format basic statistics from the given data.

    Args:
        data (list): A list of numerical data.

    Returns:
        str: A string of formatted statistics.
    """
    if not data or len(data) < 2:
        raise ValueError("At least two data points are required to compute statistics")

    if not all(isinstance(item, (int, float)) for item in data):
        raise ValueError("All data points should be numeric")

    min_data = min(data)
    max_data = max(data)

    stats_str = (
        f"Minimum: {min_data}\n"
        f"Maximum: {max_data}\n"
        f"Mean: {statistics.mean(data)}\n"
        f"Standard Deviation: {statistics.stdev(data)}"
    )
    return stats_str


class AbstractStyle:
    """
    Base class that defines the interface for scaling data into different styles.
    """

    TICKS = None

    def scale_data(self, data, verbose=False):
        """
        Abstract method for scaling data according to the selected style.

        Args:
            data (list): A list of numerical data.
            verbose (bool): Whether to include additional information in the output.

        Returns:
            list: A list of symbols representing the scaled data.
        """
        raise NotImplementedError


class ArrowsStyle(AbstractStyle):
    """
    A style class that represents data using arrows for directionality.
    """

    TICKS = ("↓", "→", "↗", "↑")

    def scale_data(self, data, verbose=False):
        result = [self.TICKS[1]]  # Assumes no change at start
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                result.append(self.TICKS[3])  # up arrow
            elif data[i] < data[i - 1]:
                result.append(self.TICKS[0])  # down arrow
            else:
                result.append(self.TICKS[1])  # right arrow for no change
        return result


class DefaultStyle(AbstractStyle):
    """
    A default style class that represents data using a set of unicode blocks.
    """

    TICKS = ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█")

    def scale_data(self, data, verbose=False):
        min_data = min(data)
        range_data = (max(data) - min_data) / (len(self.TICKS) - 1)
        if range_data == 0:
            return [self.TICKS[0] for _ in data]
        else:
            scaled_data = [self.TICKS[int(round((value - min_data) / range_data))] for value in data]
            return self.verbose_output(scaled_data) if verbose else scaled_data

    @staticmethod
    def verbose_output(scaled_data):
        """
        Constructs verbose output strings for the scaled data.

        Args:
            scaled_data (list): Scaled data points.

        Returns:
            list: Verbose description of the scaled data.
        """
        return [f"Data point {i} is {value}." for i, value in enumerate(scaled_data)]


class BlockStyle(DefaultStyle):
    """
    A style class that represents data using different block symbols.
    """

    TICKS = ("▏", "▎", "▍", "▌", "▋", "▊", "▉", "█")


class AsciiStyle(DefaultStyle):
    """
    A style class that represents data using ASCII characters.
    """

    TICKS = (".", "o", "O", "#", "@")


class NumericStyle(DefaultStyle):
    """
    A style class that represents data using numerical characters.
    """

    TICKS = ("1", "2", "3", "4", "5")


class BrailleStyle(DefaultStyle):
    """
    A style class that represents data using Braille symbols.
    """

    TICKS = ("⣀", "⣤", "⣶", "⣿")


STYLES = {
    "default": DefaultStyle,
    "block": BlockStyle,
    "ascii": AsciiStyle,
    "numeric": NumericStyle,
    "braille": BrailleStyle,
    "arrows": ArrowsStyle,
}


def print_ansi_spark(data_points, verbose=False):
    """
    Print the list of data points in the ANSI terminal.

    Args:
        data_points (list): A list of data points.
    """
    if verbose:
        print("\n".join(data_points))
    else:
        print("".join(data_points))


def get_style_instance(style):
    """
    Returns an instance of the appropriate style class based on the given style name.

    Args:
        style (str): The name of the style to use.

    Returns:
        AbstractStyle: An instance of the corresponding style class.

    Raises:
        ValueError: If the given style name is not found in the available STYLES.
    """
    if style in STYLES:
        return STYLES[style]()
    else:
        raise ValueError(f"Invalid style: {style}")


def get_args():
    """
    Parses command line arguments for the script.

    Returns:
        argparse.Namespace: Parsed command line arguments.

    Command line options:
        numbers (float): Series of data to plot.
        --ticks (str): The style of ticks to use (default, block, ascii, numeric, braille, arrows).
        --stats (bool): Show statistics about the data.
        --verbose (bool): Show verbose representation of the data.
    """
    parser = argparse.ArgumentParser(description="Process numbers")
    parser.add_argument("numbers", metavar="N", type=float, nargs="+", help="series of data to plot")
    parser.add_argument(
        "--ticks",
        choices=STYLES.keys(),
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
    return parser.parse_args()


def main():
    """
    Main function that parses command line arguments and calls the corresponding functions.
    """
    args = get_args()
    style_instance = get_style_instance(args.ticks)
    scaled_data = style_instance.scale_data(args.numbers, verbose=args.verbose)

    if args.stats:
        print(print_stats(args.numbers))

    print_ansi_spark(scaled_data, verbose=args.verbose)


if __name__ == "__main__":
    main()
