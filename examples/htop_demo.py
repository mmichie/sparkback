#!/usr/bin/env python3
"""
htop-style system monitor using sparkback braille line graphs with color support.

Displays real-time CPU, memory, and network statistics using high-resolution
braille sparklines: CPU, memory, and swap on a 0-100% scale, network from zero.

Requires psutil, from the demo extra: uv run --extra demo python examples/htop_demo.py
"""

import platform
import re
import time
from typing import Callable, List, Optional, Union

import psutil

from sparkback.spark import (
    BrailleLineGraphStyle,
    ANSI_RESET,
)

# ANSI escape codes
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# History length for graphs; each braille character shows two samples
HISTORY_LEN = 60
GRAPH_WIDTH = HISTORY_LEN // 2
BLANK = "⠀"  # an empty braille cell
ANSI_CODE = re.compile(r"\033\[[0-9;]*m")


class SystemMonitor:
    """Collects and stores system statistics history."""

    def __init__(self):
        # One history per CPU that cpu_percent reports (psutil.cpu_count() can return None)
        self.cpu_count = len(psutil.cpu_percent(percpu=True))
        self.cpu_histories = [[] for _ in range(self.cpu_count)]
        self.mem_history = []
        self.swap_history = []
        self.net_in_history = []
        self.net_out_history = []
        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()

    def update(self):
        """Collect current system stats and update histories."""
        # CPU per-core
        cpu_percents = psutil.cpu_percent(percpu=True)
        for i, pct in enumerate(cpu_percents):
            self.cpu_histories[i].append(pct)
            self.cpu_histories[i] = self.cpu_histories[i][-HISTORY_LEN:]

        # Memory
        mem = psutil.virtual_memory()
        self.mem_history.append(mem.percent)
        self.mem_history = self.mem_history[-HISTORY_LEN:]

        # Swap
        swap = psutil.swap_memory()
        self.swap_history.append(swap.percent)
        self.swap_history = self.swap_history[-HISTORY_LEN:]

        # Network (bytes per second)
        now = time.time()
        elapsed = now - self.last_time
        net = psutil.net_io_counters()

        if elapsed > 0:
            bytes_in = (net.bytes_recv - self.last_net.bytes_recv) / elapsed
            bytes_out = (net.bytes_sent - self.last_net.bytes_sent) / elapsed
            # Convert to MB/s, cap at reasonable display range
            mb_in = min(bytes_in / 1024 / 1024, 1000)
            mb_out = min(bytes_out / 1024 / 1024, 1000)
        else:
            mb_in = mb_out = 0

        self.net_in_history.append(mb_in)
        self.net_out_history.append(mb_out)
        self.net_in_history = self.net_in_history[-HISTORY_LEN:]
        self.net_out_history = self.net_out_history[-HISTORY_LEN:]

        self.last_net = net
        self.last_time = now


def render_graph(
    data: List[float], color: Union[str, Callable[[float], str]], max_value: Optional[float] = None, height: int = 3
) -> List[str]:
    """Render data as a braille graph from zero up, newest on the right.

    Until the history fills the graph, it is padded with blank cells on the left rather than made-up samples.
    color is an ANSI color for the whole graph, or a function from a value to a color, which colors each
    column by the larger of the two samples it shows.
    """
    graph = BrailleLineGraphStyle(height=height, min_value=0, max_value=max_value).scale_data(data)
    padding = BLANK * (GRAPH_WIDTH - len(graph[0]))
    if callable(color):
        colors = [color(max(data[2 * col : 2 * col + 2])) for col in range(len(graph[0]))]
        return [padding + "".join(c + char for c, char in zip(colors, row)) + ANSI_RESET for row in graph]
    return [padding + color + "".join(row) + ANSI_RESET for row in graph]


def with_prefix(prefix: str, graph: List[str]) -> List[str]:
    """Put prefix before the graph's first row and indent the other rows to line up under it."""
    indent = " " * len(ANSI_CODE.sub("", prefix))
    return [prefix + graph[0]] + [indent + row for row in graph[1:]]


def format_bar(value: float, width: int = 10, color: str = GREEN) -> str:
    """Create a simple progress bar."""
    value = max(0, min(100, value))
    filled = int(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{ANSI_RESET}"


def format_bytes(bytes_per_sec: float) -> str:
    """Format bytes/sec as human readable."""
    if bytes_per_sec < 1:
        return f"{bytes_per_sec * 1024:5.1f} KB/s"
    elif bytes_per_sec < 1024:
        return f"{bytes_per_sec:5.1f} MB/s"
    else:
        return f"{bytes_per_sec / 1024:5.1f} GB/s"


def get_color_for_value(value: float, low: float = 50, high: float = 80) -> str:
    """Get color based on value thresholds."""
    if value < low:
        return GREEN
    elif value < high:
        return YELLOW
    return RED


def print_header():
    """Print the header section."""
    hostname = platform.node() or "localhost"
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{ANSI_RESET}")
    print(
        f"{BOLD}{CYAN}║{ANSI_RESET}  {BOLD}sparkback system monitor{ANSI_RESET} - "
        f"{hostname:<40.40} {BOLD}{CYAN}║{ANSI_RESET}"
    )
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{ANSI_RESET}")
    print()


def main():
    monitor = SystemMonitor()

    # Initial CPU read (first call returns 0)
    psutil.cpu_percent(percpu=True)
    time.sleep(0.1)

    print(CLEAR_SCREEN + CURSOR_HOME + HIDE_CURSOR)
    print_header()

    try:
        while True:
            monitor.update()

            # Move cursor to position after header
            print("\033[5;1H")

            # System info
            load1, load5, load15 = psutil.getloadavg()
            uptime_secs = time.time() - psutil.boot_time()
            uptime_hours = int(uptime_secs // 3600)
            uptime_mins = int((uptime_secs % 3600) // 60)

            print(
                f"{DIM}Load: {load1:.2f} {load5:.2f} {load15:.2f}  |  "
                f"Uptime: {uptime_hours}h {uptime_mins}m  |  "
                f"Procs: {len(psutil.pids())}{ANSI_RESET}"
            )
            print()

            # CPU Section
            print(f"{BOLD}{WHITE}CPU Usage ({monitor.cpu_count} cores){ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            # Show up to 8 cores, 2 per row
            cores_per_row = 2
            for row_start in range(0, min(monitor.cpu_count, 8), cores_per_row):
                columns = []
                for i in range(row_start, min(row_start + cores_per_row, monitor.cpu_count, 8)):
                    history = monitor.cpu_histories[i]
                    current = history[-1]
                    color = get_color_for_value(current)

                    # 0-100% scale, each column colored by load like the bar
                    graph_lines = render_graph(history, get_color_for_value, max_value=100)

                    label = f"{CYAN}CPU{i:<2}{ANSI_RESET}"
                    bar = format_bar(current, 8, color)
                    pct = f"{color}{current:5.1f}%{ANSI_RESET}"
                    columns.append(with_prefix(f"{label}[{bar}]{pct} ", graph_lines))

                for lines in zip(*columns):
                    print("  ".join(lines))

            if monitor.cpu_count > 8:
                print(f"{DIM}  ... and {monitor.cpu_count - 8} more cores{ANSI_RESET}")

            print()

            # Memory Section
            print(f"{BOLD}{WHITE}Memory{ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            mem_graph = render_graph(monitor.mem_history, CYAN, max_value=100)
            mem_color = get_color_for_value(mem.percent, 60, 85)
            mem_used_gb = mem.used / 1024 / 1024 / 1024
            mem_total_gb = mem.total / 1024 / 1024 / 1024

            # Fixed-width sizes keep the memory and swap graphs in the same columns
            mem_prefix = (
                f"{GREEN}Mem {ANSI_RESET} [{format_bar(mem.percent, 8, mem_color)}] "
                f"{mem_color}{mem.percent:5.1f}%{ANSI_RESET} "
                f"{DIM}{mem_used_gb:5.1f}/{mem_total_gb:5.1f}GB{ANSI_RESET}  "
            )
            for line in with_prefix(mem_prefix, mem_graph):
                print(line)

            swap_graph = render_graph(monitor.swap_history, MAGENTA, max_value=100)
            swap_color = get_color_for_value(swap.percent, 30, 60)
            swap_used_gb = swap.used / 1024 / 1024 / 1024
            swap_total_gb = swap.total / 1024 / 1024 / 1024

            swap_prefix = (
                f"{MAGENTA}Swap{ANSI_RESET} [{format_bar(swap.percent, 8, swap_color)}] "
                f"{swap_color}{swap.percent:5.1f}%{ANSI_RESET} "
                f"{DIM}{swap_used_gb:5.1f}/{swap_total_gb:5.1f}GB{ANSI_RESET}  "
            )
            for line in with_prefix(swap_prefix, swap_graph):
                print(line)

            print()

            # Network Section
            print(f"{BOLD}{WHITE}Network I/O{ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            # From zero up to each graph's own peak
            net_in_graph = render_graph(monitor.net_in_history, GREEN)
            net_out_graph = render_graph(monitor.net_out_history, BLUE)

            current_in = monitor.net_in_history[-1]
            current_out = monitor.net_out_history[-1]

            for line in with_prefix(f"{GREEN}▼ In {ANSI_RESET} {format_bytes(current_in):>12}  ", net_in_graph):
                print(line)
            for line in with_prefix(f"{BLUE}▲ Out{ANSI_RESET} {format_bytes(current_out):>12}  ", net_out_graph):
                print(line)

            print()

            # Disk I/O, when psutil can read it on this system
            try:
                disk = psutil.disk_io_counters()
            except (OSError, RuntimeError, ValueError):  # e.g. no /proc/diskstats or /sys/block in a container
                disk = None
            if disk:
                print(f"{BOLD}{WHITE}Disk I/O{ANSI_RESET}")
                print(f"{DIM}{'─' * 72}{ANSI_RESET}")
                print(
                    f"{CYAN}Read: {ANSI_RESET} {disk.read_bytes / 1024 / 1024 / 1024:6.1f} GB total  "
                    f"{CYAN}Write:{ANSI_RESET} {disk.write_bytes / 1024 / 1024 / 1024:6.1f} GB total"
                )
                print()

            # Footer
            print(f"{DIM}Press Ctrl+C to exit | Refreshing every 1s{ANSI_RESET}")

            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR)
        print(f"\n{CYAN}Monitor stopped.{ANSI_RESET}")


if __name__ == "__main__":
    main()
