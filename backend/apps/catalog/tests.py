"""Testes do adaptador da Open Library e da busca do painel do leiloeiro."""

import time

import pytest
import requests
from django.urls import reverse

from . import open_library
from .open_library import CatalogUnavailable, search_books

BOOK_WITH_COVER = {
    "key": "/works/OL1003040W",
    "title": "Dom Casmurro",
    "author_name": ["Machado de Assis"],
    "first_publish_year": 1899,
    "edition_count": 120,
    "cover_i": 647501,
}
BOOK_WITHOUT_COVER = {
    "key": "/works/OL2W",
    "title": "Livro sem capa",
    "author_name": ["Autor Desconhecido"],
}


class FakeResponse:
    """Imita uma resposta do requests com status 200 e um JSON."""

    status_code = 200
    ok = True
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeOpenLibrary:
    """A Open Library falsa: conta as chamadas e pode fingir que caiu."""

    def __init__(self):
        self.calls = 0
        self.is_down = False
        self.payload = {"numFound": 2, "docs": [BOOK_WITH_COVER, BOOK_WITHOUT_COVER]}

    def get(self, url, *args, **kwargs):
        self.calls += 1
        if self.is_down:
            raise requests.ConnectionError("Open Library fora do ar")
        return FakeResponse(self.payload)


@pytest.fixture
def fake_api(monkeypatch):
    """Troca a Open Library de verdade pela falsa e tira a espera entre as tentativas."""
    fake = FakeOpenLibrary()
    monkeypatch.setattr(requests, "get", fake.get)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    return fake


# ---------------------------------------------------------------------------
# O adaptador
# ---------------------------------------------------------------------------


def test_search_returns_books_and_skips_the_ones_without_cover(fake_api):
    result = search_books("machado")

    assert [book.title for book in result.books] == ["Dom Casmurro"]
    assert result.books[0].cover_url.endswith("647501-L.jpg")
    assert result.is_stale is False


def test_search_uses_the_cache_for_a_repeated_query(fake_api):
    search_books("machado")
    search_books("machado")

    assert fake_api.calls == 1


def test_search_retries_and_fails_when_there_is_no_backup(fake_api):
    fake_api.is_down = True

    with pytest.raises(CatalogUnavailable):
        search_books("machado")

    assert fake_api.calls == open_library.MAX_ATTEMPTS


def test_search_falls_back_to_the_backup_when_the_api_is_down(fake_api, monkeypatch):
    # Com validade 0, a cópia "fresca" expira na hora e só a cópia de reserva fica guardada.
    monkeypatch.setattr(open_library, "CACHE_SECONDS", 0)
    search_books("machado")

    fake_api.is_down = True
    result = search_books("machado")

    assert [book.title for book in result.books] == ["Dom Casmurro"]
    assert result.is_stale is True


# ---------------------------------------------------------------------------
# A rota de busca
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("user_fixture", [None, "bidder"])
def test_search_route_is_only_for_auctioneers(api_client, request, user_fixture, db):
    if user_fixture:
        api_client.force_login(request.getfixturevalue(user_fixture))

    response = api_client.get(reverse("catalog-search"), {"q": "machado"})

    assert response.status_code == 403


def test_search_route_returns_books(api_client, auctioneer, fake_api):
    api_client.force_login(auctioneer)

    response = api_client.get(reverse("catalog-search"), {"q": "machado"})

    assert response.status_code == 200
    body = response.json()
    assert [book["title"] for book in body["results"]] == ["Dom Casmurro"]
    assert body["results"][0]["cover_url"].endswith("647501-L.jpg")
    assert body["is_stale"] is False


def test_search_route_rejects_a_one_letter_query(api_client, auctioneer, fake_api):
    api_client.force_login(auctioneer)

    response = api_client.get(reverse("catalog-search"), {"q": "m"})

    assert response.status_code == 400
    assert fake_api.calls == 0


def test_search_route_answers_503_when_the_catalog_is_down(api_client, auctioneer, fake_api):
    api_client.force_login(auctioneer)
    fake_api.is_down = True

    response = api_client.get(reverse("catalog-search"), {"q": "machado"})

    assert response.status_code == 503
    assert response.json()["code"] == "CATALOG_UNAVAILABLE"


def test_showcase_keeps_working_while_the_catalog_is_down(api_client, fake_api, db):
    fake_api.is_down = True

    response = api_client.get(reverse("lot-list"))

    assert response.status_code == 200
    assert fake_api.calls == 0