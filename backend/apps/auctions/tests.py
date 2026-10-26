"""Testes da vitrine, do painel e da criação e do cancelamento de lotes."""

from datetime import timedelta
from itertools import count
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import CatalogItemSnapshot

from .models import Lot

HOUR = timedelta(hours=1)

# Início e fim de um lote em cada fase, contados a partir de "agora".
PERIODS = {
    "live": (-HOUR, HOUR),
    "scheduled": (HOUR, 2 * HOUR),
    "finished": (-2 * HOUR, -HOUR),
}


@pytest.fixture
def make_lot(auctioneer):
    """Cria lotes direto no banco, sem passar pela Open Library."""
    numbers = count(1)

    def _make(phase="live", title="Dom Casmurro", authors=("Machado de Assis",),
              starting_price=10_000, owner=None):
        number = next(numbers)
        start_offset, end_offset = PERIODS[phase]
        now = timezone.now()
        item = CatalogItemSnapshot.objects.create(
            ol_work_key=f"/works/OL{number}W",
            title=title,
            authors=list(authors),
            first_publish_year=1899,
            edition_count=1,
            cover_source_url=f"https://covers.openlibrary.org/b/id/{number}-L.jpg",
            raw={},
        )
        return Lot.objects.create(
            auctioneer=owner or auctioneer,
            item=item,
            starting_price=starting_price,
            min_increment=500,
            starts_at=now + start_offset,
            ends_at=now + end_offset,
        )

    return _make


@pytest.fixture
def no_cover_download(monkeypatch):
    """Na criação de lotes, finge que a capa não pôde ser baixada."""
    monkeypatch.setattr("apps.auctions.services.fetch_cover", lambda book: None)


def titles(response):
    return [lot["title"] for lot in response.json()["results"]]


def lot_payload(**changes):
    now = timezone.now()
    payload = {
        "book": {
            "work_key": "/works/OL1003040W",
            "title": "Dom Casmurro",
            "authors": ["Machado de Assis"],
            "first_publish_year": 1899,
            "edition_count": 120,
            "cover_id": 647501,
        },
        "description": "Primeira edição, capa original.",
        "starting_price": 10_000,
        "min_increment": 500,
        "starts_at": (now - timedelta(minutes=1)).isoformat(),
        "ends_at": (now + HOUR).isoformat(),
    }
    payload.update(changes)
    return payload


# ---------------------------------------------------------------------------
# A vitrine (pública)
# ---------------------------------------------------------------------------


def test_showcase_is_public_and_counts_each_phase(api_client, make_lot):
    make_lot("live")
    make_lot("live")
    make_lot("scheduled")
    make_lot("finished")
    cancelled = make_lot("live")
    Lot.objects.filter(id=cancelled.id).update(status=Lot.Status.CANCELLED)

    response = api_client.get(reverse("lot-list"))

    assert response.status_code == 200
    body = response.json()
    assert body["counts"] == {"live": 2, "scheduled": 1, "finished": 1}
    assert [lot["phase"] for lot in body["results"]] == ["LIVE", "LIVE"]


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [("scheduled", "SCHEDULED"), ("finished", "ENDED")],
)
def test_showcase_filters_by_phase(api_client, make_lot, phase, expected_phase):
    make_lot("live")
    make_lot(phase)

    response = api_client.get(reverse("lot-list"), {"phase": phase})

    assert [lot["phase"] for lot in response.json()["results"]] == [expected_phase]


def test_showcase_lists_live_lots_ending_soonest_first(api_client, make_lot):
    later = make_lot("live", title="Termina depois")
    sooner = make_lot("live", title="Termina antes")
    Lot.objects.filter(id=later.id).update(ends_at=timezone.now() + 2 * HOUR)
    Lot.objects.filter(id=sooner.id).update(ends_at=timezone.now() + HOUR / 2)

    response = api_client.get(reverse("lot-list"))

    assert titles(response) == ["Termina antes", "Termina depois"]


@pytest.mark.parametrize("term", ["casmurro", "MACHADO"])
def test_showcase_searches_title_and_author(api_client, make_lot, term):
    make_lot(title="Dom Casmurro", authors=["Machado de Assis"])
    make_lot(title="O Cortiço", authors=["Aluisio Azevedo"])

    response = api_client.get(reverse("lot-list"), {"q": term})

    assert titles(response) == ["Dom Casmurro"]


@pytest.mark.parametrize(
    ("filters", "expected"),
    [({"min_price": 20_000}, ["Com lances"]), ({"max_price": 15_000}, ["Sem lances"])],
)
def test_showcase_price_range_uses_the_current_bid(api_client, make_lot, filters, expected):
    make_lot(title="Sem lances", starting_price=10_000)
    with_bids = make_lot(title="Com lances", starting_price=5_000)
    Lot.objects.filter(id=with_bids.id).update(current_price=30_000, bid_count=3)

    response = api_client.get(reverse("lot-list"), filters)

    assert titles(response) == expected


def test_showcase_rejects_an_unknown_phase(api_client, db):
    response = api_client.get(reverse("lot-list"), {"phase": "errada"})

    assert response.status_code == 400
    assert "phase" in response.json()


def test_showcase_shows_only_the_leader_alias(api_client, make_lot, bidder):
    lot = make_lot()
    Lot.objects.filter(id=lot.id).update(leader=bidder, current_price=12_000, bid_count=1)

    response = api_client.get(reverse("lot-list"))

    assert response.json()["results"][0]["leader_alias"] == bidder.public_alias
    assert bidder.email not in response.content.decode()
    assert bidder.name not in response.content.decode()


def test_lot_detail_is_public(api_client, make_lot):
    lot = make_lot()

    response = api_client.get(reverse("lot-detail", args=[lot.id]))

    assert response.status_code == 200
    assert response.json()["title"] == "Dom Casmurro"


def test_lot_detail_answers_404_for_an_unknown_lot(api_client, db):
    response = api_client.get(reverse("lot-detail", args=[uuid4()]))

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# O painel do leiloeiro
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("user_fixture", [None, "bidder"])
def test_dashboard_is_only_for_auctioneers(api_client, request, user_fixture, db):
    if user_fixture:
        api_client.force_login(request.getfixturevalue(user_fixture))

    response = api_client.get(reverse("auctioneer-lots"))

    assert response.status_code == 403


def test_dashboard_shows_only_my_lots_and_the_summary(
    api_client, auctioneer, other_auctioneer, make_lot
):
    make_lot("live")
    make_lot("scheduled")
    make_lot("finished")
    make_lot("live", title="Lote do outro", owner=other_auctioneer)
    api_client.force_login(auctioneer)

    response = api_client.get(reverse("auctioneer-lots"))

    body = response.json()
    assert "Lote do outro" not in titles(response)
    assert len(body["results"]) == 3
    assert body["summary"] == {"live": 1, "scheduled": 1, "finished": 1, "total_received": 0}


# ---------------------------------------------------------------------------
# Criar um lote
# ---------------------------------------------------------------------------


def test_auctioneer_creates_a_lot(api_client, auctioneer, no_cover_download):
    api_client.force_login(auctioneer)

    response = api_client.post(reverse("auctioneer-lots"), lot_payload(), format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Dom Casmurro"
    assert body["phase"] == "LIVE"
    assert body["cover_url"] == "https://covers.openlibrary.org/b/id/647501-L.jpg"
    assert Lot.objects.get().auctioneer == auctioneer


def test_creating_a_lot_keeps_a_local_copy_of_the_cover(
    api_client, auctioneer, monkeypatch, settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path
    monkeypatch.setattr("apps.auctions.services.fetch_cover", lambda book: b"jpeg-falso")
    api_client.force_login(auctioneer)

    response = api_client.post(reverse("auctioneer-lots"), lot_payload(), format="json")

    assert "covers/647501" in response.json()["cover_url"]
    assert (tmp_path / "covers" / "647501.jpg").read_bytes() == b"jpeg-falso"


def test_bidder_cannot_create_a_lot(api_client, bidder, no_cover_download):
    api_client.force_login(bidder)

    response = api_client.post(reverse("auctioneer-lots"), lot_payload(), format="json")

    assert response.status_code == 403
    assert not Lot.objects.exists()


@pytest.mark.parametrize(
    ("starts_in", "ends_in", "code"),
    [
        (2 * HOUR, HOUR, "LOT_INVALID_PERIOD"),
        (-2 * HOUR, -HOUR, "LOT_ENDS_IN_PAST"),
    ],
)
def test_lot_period_must_make_sense(
    api_client, auctioneer, no_cover_download, starts_in, ends_in, code
):
    now = timezone.now()
    api_client.force_login(auctioneer)
    payload = lot_payload(
        starts_at=(now + starts_in).isoformat(),
        ends_at=(now + ends_in).isoformat(),
    )

    response = api_client.post(reverse("auctioneer-lots"), payload, format="json")

    assert response.status_code == 422
    assert response.json()["code"] == code
    assert not Lot.objects.exists()


def test_lot_needs_a_valid_open_library_book(api_client, auctioneer, no_cover_download):
    api_client.force_login(auctioneer)
    payload = lot_payload()
    payload["book"]["work_key"] = "qualquer-coisa"

    response = api_client.post(reverse("auctioneer-lots"), payload, format="json")

    assert response.status_code == 400
    assert "book" in response.json()


# ---------------------------------------------------------------------------
# Cancelar um lote
# ---------------------------------------------------------------------------


def cancel(api_client, lot):
    return api_client.post(reverse("auctioneer-lot-cancel", args=[lot.id]))


def test_auctioneer_cancels_a_lot_without_bids(api_client, auctioneer, make_lot):
    lot = make_lot("scheduled")
    api_client.force_login(auctioneer)

    response = cancel(api_client, lot)

    assert response.status_code == 200
    assert response.json()["phase"] == "CANCELLED"
    lot.refresh_from_db()
    assert lot.status == Lot.Status.CANCELLED


def test_auctioneer_cannot_cancel_someone_elses_lot(api_client, other_auctioneer, make_lot):
    lot = make_lot()
    api_client.force_login(other_auctioneer)

    response = cancel(api_client, lot)

    assert response.status_code == 404
    lot.refresh_from_db()
    assert lot.status == Lot.Status.OPEN


def test_lot_with_bids_cannot_be_cancelled(api_client, auctioneer, make_lot):
    lot = make_lot()
    Lot.objects.filter(id=lot.id).update(bid_count=1)
    api_client.force_login(auctioneer)

    response = cancel(api_client, lot)

    assert response.status_code == 422
    assert response.json()["code"] == "LOT_HAS_BIDS"
    assert response.json()["data"] == {"bid_count": 1}


def test_finished_lot_cannot_be_cancelled(api_client, auctioneer, make_lot):
    lot = make_lot("finished")
    api_client.force_login(auctioneer)

    response = cancel(api_client, lot)

    assert response.status_code == 422
    assert response.json()["code"] == "LOT_ALREADY_FINISHED"