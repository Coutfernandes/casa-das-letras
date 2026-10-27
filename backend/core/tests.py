"""Testes das ferramentas compartilhadas do core."""

import pytest

from .money import format_brl


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (0, "R$ 0,00"),
        (5, "R$ 0,05"),
        (125_000, "R$ 1.250,00"),
        (100_000_00, "R$ 100.000,00"),
    ],
)
def test_format_brl(cents, expected):
    assert format_brl(cents) == expected
