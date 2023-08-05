# flake8: noqa
# pylint: skip-file
# mypy: ignore-errors

import sparkback.spark as spark


def test_scale_data_default():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    style_instance = spark.DefaultStyle()
    expected_output = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    assert style_instance.scale_data(data) == expected_output


def test_scale_data_block():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    style_instance = spark.BlockStyle()
    expected_output = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    assert style_instance.scale_data(data) == expected_output


def test_scale_data_arrows():
    data = [1, 2, 3, 2, 2, 7, 6]
    style_instance = spark.ArrowsStyle()
    expected_output = ["→", "↑", "↑", "↓", "→", "↑", "↓"]
    assert style_instance.scale_data(data) == expected_output


def test_print_stats():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    expected_output = "Minimum: 1\nMaximum: 8\nMean: 4.5\nStandard Deviation: 2.449489742783178"
    assert spark.print_stats(data) == expected_output
