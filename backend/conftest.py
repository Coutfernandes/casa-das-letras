"""Peças compartilhadas pelos testes de todos os apps."""

import pytest
from rest_framework.test import APIClient

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