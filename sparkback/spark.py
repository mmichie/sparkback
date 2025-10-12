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
from typing import List, Union, Tuple


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


class MultiLineGraphStyle(AbstractStyle):
    """
    A style class that represents data as a multiline graph using Unicode characters.
    """

    def scale_data(self, data, verbose=False):
        min_data = min(data)
        max_data = max(data)
        range_data = max_data - min_data
        graph_height = 10  # Set graph height to 10 lines for better visibility

        if range_data == 0:
            return [["─" * len(data)] * graph_height]  # Uniform line if no variation

        scaled_data = [int((value - min_data) / range_data * (graph_height - 1)) for value in data]

        # Initialize the graph canvas
        graph = [[" " for _ in range(len(data))] for _ in range(graph_height)]

        # Place the points on the graph
        for idx, height in enumerate(scaled_data):
            for y in range(graph_height):
                graph[y][idx] = "█" if y >= graph_height - height else " "

        return graph

    def __str__(self):
        return "Multiline Graph Style"


class LineGraphStyle(AbstractStyle):
    """
    A style class that draws connected line graphs using Unicode box-drawing characters.

    This style connects consecutive data points with lines, supporting horizontal,
    vertical, and diagonal segments. The graph is rendered on a configurable height
    canvas using Unicode characters: ─│╱╲● for different line directions.
    """

    def __init__(self, height: int = 10) -> None:
        """
        Initialize the LineGraphStyle with a specified graph height.

        Args:
            height: The number of rows in the graph canvas. Must be >= 2.

        Raises:
            ValueError: If height is less than 2.
        """
        if height < 2:
            raise ValueError("Graph height must be at least 2")
        self.height = height

    def scale_data(self, data: List[Union[int, float]], verbose: bool = False) -> List[List[str]]:
        """
        Scale data and render as a connected line graph.

        Args:
            data: A list of numerical values to plot.
            verbose: If True, includes additional debug information (currently unused).

        Returns:
            A 2D list of strings representing the graph, with graph[0] as the top row.

        Raises:
            ValueError: If data is empty or contains non-numeric values.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        if len(data) == 1:
            # Single point: draw just a point in the middle
            graph = [[" " for _ in range(1)] for _ in range(self.height)]
            mid_y = self.height // 2
            graph[mid_y][0] = "●"
            return graph

        # Scale data to fit within graph height
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            # All values are the same: draw horizontal line at midpoint
            y_pos = self.height // 2
            graph = [[" " for _ in range(len(data))] for _ in range(self.height)]
            for x in range(len(data)):
                graph[y_pos][x] = "─"
            # Mark endpoints
            graph[y_pos][0] = "●"
            graph[y_pos][len(data) - 1] = "●"
            return graph

        # Scale each value to [0, height-1], inverted so top of graph is max value
        scaled_points: List[int] = [int((val - min_val) / range_val * (self.height - 1)) for val in data]

        # Initialize the graph canvas
        graph: List[List[str]] = [[" " for _ in range(len(data))] for _ in range(self.height)]

        # Draw lines between consecutive points
        for i in range(len(scaled_points) - 1):
            x1, y1 = i, scaled_points[i]
            x2, y2 = i + 1, scaled_points[i + 1]

            # Invert y-coordinates so 0 is at top of graph
            y1_inv = self.height - 1 - y1
            y2_inv = self.height - 1 - y2

            self._draw_line(graph, x1, y1_inv, x2, y2_inv)

        # Mark endpoints
        first_y = self.height - 1 - scaled_points[0]
        last_y = self.height - 1 - scaled_points[-1]
        graph[first_y][0] = "●"
        graph[last_y][len(data) - 1] = "●"

        return graph

    def _draw_line(self, graph: List[List[str]], x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Draw a line between two points on the graph canvas.

        Uses Unicode box-drawing characters to represent different line directions:
        - ─ for horizontal lines
        - │ for vertical lines
        - ╱ for diagonal up-right lines
        - ╲ for diagonal down-right lines

        Args:
            graph: The 2D graph canvas to draw on (modified in place).
            x1: Starting x-coordinate.
            y1: Starting y-coordinate.
            x2: Ending x-coordinate.
            y2: Ending y-coordinate.
        """
        dx = x2 - x1
        dy = y2 - y1

        # For adjacent x coordinates (dx=1), determine the character
        if dx == 1:
            if dy == 0:
                # Horizontal line
                if graph[y1][x1] == " ":
                    graph[y1][x1] = "─"
                if graph[y2][x2] == " ":
                    graph[y2][x2] = "─"
            elif dy > 0:
                # Going down (down-right diagonal)
                steps = abs(dy)
                for step in range(steps + 1):
                    y = y1 + step
                    if 0 <= y < len(graph):
                        if step == 0 or step == steps:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "╲" if dy == 1 else "│"
                        else:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "│"
            else:
                # Going up (up-right diagonal)
                steps = abs(dy)
                for step in range(steps + 1):
                    y = y1 - step
                    if 0 <= y < len(graph):
                        if step == 0 or step == steps:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "╱" if dy == -1 else "│"
                        else:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "│"

    def __str__(self) -> str:
        """Return a string representation of this style."""
        return f"Line Graph Style (height={self.height})"


STYLES = {
    "default": DefaultStyle,
    "block": BlockStyle,
    "ascii": AsciiStyle,
    "numeric": NumericStyle,
    "braille": BrailleStyle,
    "arrows": ArrowsStyle,
    "multiline": MultiLineGraphStyle,
    "line": LineGraphStyle,
}


def print_ansi_spark(data_points, verbose=False, style=None):
    """
    Print the list of data points in the ANSI terminal, formatted according to the specified style.

    Args:
        data_points (list or list of lists): A list of data points or a list of lists for multiline graphs.
        verbose (bool): Whether to print verbose output.
        style (str): The style of the graph, which could influence formatting details.
    """
    if isinstance(data_points[0], list):
        if verbose:
            for index, line in enumerate(data_points):
                print(f"Line {index+1}: {''.join(line)}")
        else:
            for line in data_points:
                print("".join(line))
    else:
        if verbose:
            for index, point in enumerate(data_points):
                print(f"Point {index+1}: {point}")
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
