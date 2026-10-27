"""Peças compartilhadas pelos testes de todos os apps."""

import pytest
from rest_framework.test import APIClient
from django.core.cache import cache
from apps.accounts.models import User
from datetime import timedelta
from itertools import count

from django.utils import timezone

from apps.auctions.models import Lot
from apps.catalog.models import CatalogItemSnapshot

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
