#!/usr/bin/env python3
"""
htop-style demo using sparkback braille line graphs with color support.

This demo simulates a system monitor displaying CPU cores, memory usage,
and network activity using high-resolution braille sparklines.
"""

import random
import sys
import time

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from sparkback.spark import (
    BrailleLineGraphStyle,
    apply_color_to_output,
    ANSI_RESET,
)

# ANSI escape codes for cursor control and colors
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"


def generate_cpu_data(history: list, load_bias: float = 0.5) -> list:
    """Generate realistic CPU usage data with some continuity."""
    if not history:
        history = [random.uniform(20, 60) for _ in range(40)]

    # Add new value with some continuity from last value
    last = history[-1]
    change = random.gauss(0, 10) + (load_bias - 0.5) * 5
    new_val = max(0, min(100, last + change))
    history.append(new_val)

    # Keep only last 40 values
    return history[-40:]


def generate_mem_data(base: float = 45) -> list:
    """Generate memory-like data (more stable than CPU)."""
    data = []
    val = base
    for _ in range(40):
        val += random.gauss(0, 2)
        val = max(base - 10, min(base + 15, val))
        data.append(val)
    return data


def render_graph(data: list, height: int = 4, color_scheme: str = "gradient") -> list:
    """Render data as a colored braille graph."""
    style = BrailleLineGraphStyle(height=height)
    graph = style.scale_data(data)
    colored = apply_color_to_output(graph, data, color_scheme)
    return ["".join(row) for row in colored]


def format_bar(value: float, width: int = 20, color: str = GREEN) -> str:
    """Create a simple progress bar."""
    filled = int(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{ANSI_RESET}"


def print_header():
    """Print the header section."""
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════╗{ANSI_RESET}")
    print(f"{BOLD}{CYAN}║{ANSI_RESET}  {BOLD}sparkback htop-style demo{ANSI_RESET}                                   {BOLD}{CYAN}║{ANSI_RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════╝{ANSI_RESET}")
    print()


def main():
    # Initialize data histories for each CPU core
    num_cores = 4
    cpu_histories = [[] for _ in range(num_cores)]
    cpu_biases = [random.uniform(0.3, 0.7) for _ in range(num_cores)]

    # Memory base values
    mem_used = random.uniform(40, 60)
    swap_used = random.uniform(5, 20)

    print(CLEAR_SCREEN + CURSOR_HOME)
    print_header()

    try:
        for frame in range(100):
            # Move cursor to position after header
            print(f"\033[5;1H")  # Row 5, Column 1

            # Update CPU data
            for i in range(num_cores):
                cpu_histories[i] = generate_cpu_data(cpu_histories[i], cpu_biases[i])
                # Slowly drift the bias
                cpu_biases[i] += random.gauss(0, 0.02)
                cpu_biases[i] = max(0.2, min(0.8, cpu_biases[i]))

            # CPU Section
            print(f"{BOLD}{WHITE}CPU Usage{ANSI_RESET}")
            print(f"{DIM}{'─' * 62}{ANSI_RESET}")

            for i in range(num_cores):
                current = cpu_histories[i][-1]
                graph_lines = render_graph(cpu_histories[i], height=2, color_scheme="gradient")

                # Print core label and current value
                color = GREEN if current < 50 else (YELLOW if current < 80 else RED)
                print(f"{CYAN}CPU{i}{ANSI_RESET} [{format_bar(current, 10, color)}] {color}{current:5.1f}%{ANSI_RESET}  ", end="")
                print(graph_lines[0])
                print(f"{'':34}", end="")
                print(graph_lines[1])

            print()

            # Memory Section
            print(f"{BOLD}{WHITE}Memory{ANSI_RESET}")
            print(f"{DIM}{'─' * 62}{ANSI_RESET}")

            mem_used += random.gauss(0, 0.5)
            mem_used = max(30, min(80, mem_used))
            mem_data = generate_mem_data(mem_used)
            mem_graph = render_graph(mem_data, height=2, color_scheme="cyan")

            print(f"{GREEN}Mem{ANSI_RESET}  [{format_bar(mem_used, 10, GREEN)}] {GREEN}{mem_used:5.1f}%{ANSI_RESET}  ", end="")
            print(mem_graph[0])
            print(f"{'':34}", end="")
            print(mem_graph[1])

            swap_used += random.gauss(0, 0.2)
            swap_used = max(2, min(30, swap_used))
            swap_data = generate_mem_data(swap_used)
            swap_graph = render_graph(swap_data, height=2, color_scheme="magenta")

            print(f"{MAGENTA}Swap{ANSI_RESET} [{format_bar(swap_used, 10, MAGENTA)}] {MAGENTA}{swap_used:5.1f}%{ANSI_RESET}  ", end="")
            print(swap_graph[0])
            print(f"{'':34}", end="")
            print(swap_graph[1])

            print()

            # Network Section
            print(f"{BOLD}{WHITE}Network I/O{ANSI_RESET}")
            print(f"{DIM}{'─' * 62}{ANSI_RESET}")

            net_in = [random.uniform(10, 90) for _ in range(40)]
            net_out = [random.uniform(5, 60) for _ in range(40)]

            net_in_graph = render_graph(net_in, height=2, color_scheme="green")
            net_out_graph = render_graph(net_out, height=2, color_scheme="blue")

            print(f"{GREEN}▼ In {ANSI_RESET} {net_in[-1]:5.1f} MB/s              ", end="")
            print(net_in_graph[0])
            print(f"{'':34}", end="")
            print(net_in_graph[1])

            print(f"{BLUE}▲ Out{ANSI_RESET} {net_out[-1]:5.1f} MB/s              ", end="")
            print(net_out_graph[0])
            print(f"{'':34}", end="")
            print(net_out_graph[1])

            print()
            print(f"{DIM}Frame {frame + 1}/100 - Press Ctrl+C to exit{ANSI_RESET}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n{CYAN}Demo ended.{ANSI_RESET}")


if __name__ == "__main__":
    main()
