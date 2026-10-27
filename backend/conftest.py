"""Peças compartilhadas pelos testes de todos os apps."""

import pytest
from rest_framework.test import APIClient
from django.core.cache import cache
from apps.accounts.models import User

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
