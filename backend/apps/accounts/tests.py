"""Testes da autenticação, das permissões por papel e dos pseudônimos."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from apps.accounts.aliases import build_public_alias
from apps.accounts.models import User
from apps.accounts.permissions import IsAuctioneer, IsBidder
from conftest import PASSWORD

REGISTER_URL = reverse("auth-register")
LOGIN_URL = reverse("auth-login")
LOGOUT_URL = reverse("auth-logout")
ME_URL = reverse("auth-me")
CSRF_URL = reverse("auth-csrf")

VALID_REGISTRATION = {
    "email": "bruno@exemplo.com",
    "name": "Bruno",
    "role": "BIDDER",
    "password": PASSWORD,
}


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cadastro_cria_usuario_e_ja_deixa_logado(api_client):
    response = api_client.post(REGISTER_URL, VALID_REGISTRATION, format="json")

    assert response.status_code == 201
    assert "password" not in response.data
    assert response.data["public_alias"].startswith("Licitante #")
    assert api_client.get(ME_URL).status_code == 200


@pytest.mark.django_db
def test_cadastro_guarda_email_em_minusculas(api_client):
    data = {**VALID_REGISTRATION, "email": "  Bruno@EXEMPLO.com "}

    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 201
    assert response.data["email"] == "bruno@exemplo.com"


def test_cadastro_recusa_email_repetido_mesmo_com_maiusculas(api_client, make_user):
    make_user(email="bruno@exemplo.com")
    data = {**VALID_REGISTRATION, "email": "BRUNO@exemplo.com"}

    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_cadastro_recusa_senha_fraca(api_client):
    data = {**VALID_REGISTRATION, "password": "12345678"}

    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_cadastro_recusa_papel_invalido(api_client):
    data = {**VALID_REGISTRATION, "role": "ADMIN"}

    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400
    assert "role" in response.data


# ---------------------------------------------------------------------------
# Login, logout e "quem sou eu"
# ---------------------------------------------------------------------------


def test_login_com_senha_certa(api_client, make_user):
    make_user(email="ana@exemplo.com")

    response = api_client.post(
        LOGIN_URL, {"email": "ANA@exemplo.com", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 200
    assert response.data["email"] == "ana@exemplo.com"


def test_login_com_senha_errada_nao_revela_se_o_email_existe(api_client, make_user):
    make_user(email="ana@exemplo.com")

    senha_errada = api_client.post(
        LOGIN_URL, {"email": "ana@exemplo.com", "password": "errada"}, format="json"
    )
    email_inexistente = api_client.post(
        LOGIN_URL, {"email": "ninguem@exemplo.com", "password": "errada"}, format="json"
    )

    assert senha_errada.status_code == email_inexistente.status_code == 400
    assert senha_errada.data == email_inexistente.data


def test_login_recusa_conta_desativada(api_client, make_user):
    make_user(email="ana@exemplo.com", is_active=False)

    response = api_client.post(
        LOGIN_URL, {"email": "ana@exemplo.com", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_quem_sou_eu_exige_login(api_client):
    assert api_client.get(ME_URL).status_code == 403


def test_logout_encerra_a_sessao(api_client, make_user):
    api_client.force_login(make_user())

    assert api_client.post(LOGOUT_URL).status_code == 204
    assert api_client.get(ME_URL).status_code == 403


def test_login_exige_token_csrf(make_user):
    make_user(email="ana@exemplo.com")
    client = APIClient(enforce_csrf_checks=True)
    credentials = {"email": "ana@exemplo.com", "password": PASSWORD}

    sem_token = client.post(LOGIN_URL, credentials, format="json")

    client.get(CSRF_URL)
    token = client.cookies["csrftoken"].value
    com_token = client.post(LOGIN_URL, credentials, format="json", HTTP_X_CSRFTOKEN=token)

    assert sem_token.status_code == 403
    assert com_token.status_code == 200


# ---------------------------------------------------------------------------
# Permissões por papel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "auctioneer_allowed", "bidder_allowed"),
    [
        (User.Role.AUCTIONEER, True, False),
        (User.Role.BIDDER, False, True),
    ],
)
def test_permissoes_por_papel(make_user, role, auctioneer_allowed, bidder_allowed):
    request = APIRequestFactory().get("/")
    request.user = make_user(role=role)

    assert IsAuctioneer().has_permission(request, view=None) is auctioneer_allowed
    assert IsBidder().has_permission(request, view=None) is bidder_allowed


def test_permissoes_recusam_visitante_sem_login():
    request = APIRequestFactory().get("/")
    request.user = AnonymousUser()

    assert IsAuctioneer().has_permission(request, view=None) is False
    assert IsBidder().has_permission(request, view=None) is False


# ---------------------------------------------------------------------------
# Pseudônimo
# ---------------------------------------------------------------------------


def test_pseudonimo_e_sempre_o_mesmo_para_o_mesmo_usuario(make_user):
    user = make_user()

    assert user.public_alias == build_public_alias(user.id)


def test_pseudonimo_depende_do_segredo(settings, make_user):
    user = make_user()
    original = build_public_alias(user.id)

    settings.ALIAS_SECRET = "outro-segredo"

    assert build_public_alias(user.id) != original