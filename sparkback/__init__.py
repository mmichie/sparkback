
# -*- coding: utf-8 -*-
import sys

ticks = ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█')

def scale_data(d):
    data_range = max(d) - min(d)
    divider = data_range / (len(ticks) - 1)

    min_value = min(d)

    scaled = [int(abs(round((i - min_value) / divider))) for i in d]

    return scaled

def print_ansi_spark(d):
    for i in d:
        sys.stdout.write(ticks[i])
    print ''

if __name__ == "__main__":
    print 'hello world'
