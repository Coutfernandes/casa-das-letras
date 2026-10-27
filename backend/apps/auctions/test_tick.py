"""Testes da rota que o cron-job.org chama a cada minuto: POST /api/internal/tick/."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.audit import anchors
from apps.bids.services import place_bid
from apps.wallet.services import deposit

from .models import Lot

SECRET = "segredo-dos-testes"


@pytest.fixture
def cron_secret(settings):
    settings.CRON_SECRET = SECRET


def tick(api_client, authorization=None):
    headers = {"HTTP_AUTHORIZATION": authorization} if authorization is not None else {}
    return api_client.post(reverse("internal-tick"), **headers)


def test_without_cron_secret_the_route_is_off(api_client, settings):
    settings.CRON_SECRET = ""

    response = tick(api_client, f"Bearer {SECRET}")

    assert response.status_code == 404


@pytest.mark.parametrize("authorization", [None, "", "Bearer errado", SECRET, f"Basic {SECRET}"])
def test_missing_or_wrong_secret_is_forbidden(api_client, cron_secret, ended_lot, authorization):
    response = tick(api_client, authorization)

    assert response.status_code == 403
    ended_lot.refresh_from_db()
    assert ended_lot.status == Lot.Status.OPEN


def test_only_post_is_accepted(api_client, cron_secret):
    response = api_client.get(reverse("internal-tick"), HTTP_AUTHORIZATION=f"Bearer {SECRET}")

    assert response.status_code == 405


def test_with_the_secret_it_settles_due_lots(api_client, cron_secret, ended_lot, make_lot):
    running = make_lot("live")

    response = tick(api_client, f"Bearer {SECRET}")

    assert response.status_code == 200
    assert response.json()["settled"] == 1
    ended_lot.refresh_from_db()
    running.refresh_from_db()
    assert ended_lot.status == Lot.Status.CLOSED
    assert running.status == Lot.Status.OPEN


def test_it_restores_an_anchor_that_fell_behind(api_client, cron_secret, make_lot, bidder):
    # Nos testes, o on_commit não roda: o lance vale, mas a cópia no Redis fica para trás.
    deposit(bidder, 100_000)
    lot = make_lot("live")
    place_bid(lot.id, bidder, 10_000)
    assert anchors.last_anchor(lot.id) is None

    response = tick(api_client, f"Bearer {SECRET}")

    assert response.json() == {"settled": 0, "restored": 1}
    assert anchors.last_anchor(lot.id)["bid_count"] == 1


def test_lots_without_recent_bids_are_not_checked(api_client, cron_secret, make_lot, bidder):
    """Poupa a cota do Upstash: um lote cujo último lance tem mais de 24 horas fica de fora."""
    deposit(bidder, 100_000)
    lot = make_lot("live")
    now = timezone.now()
    Lot.objects.filter(id=lot.id).update(starts_at=now - timedelta(days=3))
    place_bid(lot.id, bidder, 10_000, now=now - timedelta(days=2))

    response = tick(api_client, f"Bearer {SECRET}")

    assert response.json() == {"settled": 0, "restored": 0}
    assert anchors.last_anchor(lot.id) is None
