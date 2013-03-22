# -*- coding: utf-8 -*-
from __future__ import division
import argparse

ticks = ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█')

def scale_data(data):
    m = min(data)
    n = (max(data) - m) / (len(ticks) - 1)
  
    print m,n

    return [ ticks[int((t - m) / n)] for t in data ]

def print_ansi_spark(d):
    print ''.join(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    args = parser.parse_args()
    print_ansi_spark(scale_data(args.integers))


