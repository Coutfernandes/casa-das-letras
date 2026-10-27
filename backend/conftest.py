"""Peças compartilhadas pelos testes de todos os apps."""

from datetime import timedelta
from itertools import count

import fakeredis
import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit import anchors
from apps.audit.signing import generate_key_text
from apps.auctions.models import Lot
from apps.bids.services import place_bid
from apps.catalog.models import CatalogItemSnapshot
from apps.wallet.services import deposit

PASSWORD = "SenhaSegura123!"


@pytest.fixture
def api_client():
    """Cliente que faz requisições à API como um navegador faria."""
    return APIClient()


@pytest.fixture
def make_user(db):
    """Fábrica de usuários. Uso: make_user(), make_user(role=User.Role.AUCTIONEER)."""

    def _make_user(email="ana@exemplo.com", name="Ana", role=User.Role.BIDDER, **extra):
        return User.objects.create_user(
            email=email, password=PASSWORD, name=name, role=role, **extra
        )

    return _make_user

@pytest.fixture(autouse=True)
def clear_cache():
    """Cada teste começa com o cache vazio, para um não ver o que o outro guardou."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def fake_redis(settings, monkeypatch):
    """Cada teste tem uma chave de assinatura nova e um Redis de mentira, vazio, na memória."""
    settings.AUDIT_SIGNING_KEY = generate_key_text()
    settings.REDIS_URL = "redis://redis-dos-testes:6379/0"
    client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(anchors, "_connect", lambda url: client)
    return client


@pytest.fixture
def auctioneer(db):
    return User.objects.create_user(
        email="leiloeiro@exemplo.com",
        password=PASSWORD,
        name="Ana Leiloeira",
        role=User.Role.AUCTIONEER,
    )


@pytest.fixture
def other_auctioneer(db):
    return User.objects.create_user(
        email="outro.leiloeiro@exemplo.com",
        password=PASSWORD,
        name="Carlos Leiloeiro",
        role=User.Role.AUCTIONEER,
    )


@pytest.fixture
def bidder(db):
    return User.objects.create_user(
        email="licitante@exemplo.com",
        password=PASSWORD,
        name="Bruno Licitante",
        role=User.Role.BIDDER,
    )

@pytest.fixture
def other_bidder(db):
    return User.objects.create_user(
        email="segundo.licitante@exemplo.com",
        password=PASSWORD,
        name="Carla Licitante",
        role=User.Role.BIDDER,
    )


# Início e fim de um lote em cada fase, contados a partir de "agora".
LOT_PERIODS = {
    "live": (timedelta(hours=-1), timedelta(hours=1)),
    "scheduled": (timedelta(hours=1), timedelta(hours=2)),
    "finished": (timedelta(hours=-2), timedelta(hours=-1)),
}


@pytest.fixture
def make_lot(auctioneer):
    """Cria lotes direto no banco, sem passar pela Open Library."""
    numbers = count(1)

    def _make(phase="live", title="Dom Casmurro", authors=("Machado de Assis",),
              starting_price=10_000, owner=None):
        number = next(numbers)
        start_offset, end_offset = LOT_PERIODS[phase]
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
def end_now():
    """Faz um lote terminar agora, como se o tempo tivesse passado. Uso: end_now(lot)."""

    def _end_now(lot):
        Lot.objects.filter(id=lot.id).update(ends_at=timezone.now() - timedelta(seconds=1))

    return _end_now


@pytest.fixture
def ended_lot(make_lot, end_now, bidder, other_bidder):
    """Um lote com dois lances (o outro licitante venceu com R$ 120), que acabou de terminar."""
    deposit(bidder, 100_000)
    deposit(other_bidder, 100_000)
    lot = make_lot()
    place_bid(lot.id, bidder, 10_000)
    place_bid(lot.id, other_bidder, 12_000)
    end_now(lot)
    return lot
