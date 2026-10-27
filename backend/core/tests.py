"""Testes das ferramentas compartilhadas do core."""

import pytest
from django.urls import reverse

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


@pytest.mark.django_db
def test_health_answers_without_login(api_client, django_assert_num_queries):
    with django_assert_num_queries(0):
        response = api_client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
