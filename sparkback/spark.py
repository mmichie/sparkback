# -*- coding: utf-8 -*-
from __future__ import division

ansi_ticks = ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█')

def scale_data(data, ticks):
    m = min(data)
    n = (max(data) - m) / (len(ticks) - 1)

    # if every element is the same height return all lower ticks, else compute
    # the tick height
    if n == 0: 
        return ( ticks[0] for t in data )
    else: 
        return ( ticks[int(round((t - m) / n))] for t in data )

def print_ansi_spark(d):
    print ''.join(d)
