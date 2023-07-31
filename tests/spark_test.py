import pytest
import sparkback.spark as spark

def test_scale_data_default():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    ticks = spark.TICKS_OPTIONS["default"]
    expected_output = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    assert list(spark.scale_data(data, ticks, "default")) == expected_output

def test_scale_data_arrows():
    data = [1, 2, 3, 2, 2, 7, 6]
    ticks = spark.TICKS_OPTIONS["arrows"]
    expected_output = ['↑', '↑', '↓', '→', '↑', '↓']
    assert spark.scale_data(data, ticks, "arrows") == expected_output

def test_print_stats():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    expected_output = "Minimum: 1\nMaximum: 8\nMean: 4.5\nStandard Deviation: 2.449489742783178"
    assert spark.print_stats(data) == expected_output

