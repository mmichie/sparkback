# -*- coding: utf-8 -*-
from __future__ import division
import argparse

ansi_ticks = ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█')

def scale_data(data, ticks):
    m = min(data)
    n = (max(data) - m) / (len(ticks) - 1)

    # if every element is the same height return all lower ticks, else compute
    # the tick height
    if n == 0: 
        return [ ticks[0] for t in data]
    else: 
        return [ ticks[int((t - m) / n)] for t in data ]

def print_ansi_spark(d):
    print ''.join(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process numbers')
    parser.add_argument('numbers', metavar='N', type=float, nargs='+',
                        help='series of data to plot')
    args = parser.parse_args()
    print_ansi_spark(scale_data(args.numbers, ansi_ticks))
