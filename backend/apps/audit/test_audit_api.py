"""Testes das rotas públicas da auditoria: abrem sem login e nunca revelam quem deu os lances."""

import uuid

from django.urls import reverse

from apps.auctions.models import Lot


def audit_url(lot_id):
    return reverse("audit-lot", args=[lot_id])


def test_audit_opens_without_login_and_shows_only_aliases(api_client, ended_lot, bidder, other_bidder):
    response = api_client.get(audit_url(ended_lot.id))

    assert response.status_code == 200
    body = response.json()
    assert body["lot"]["id"] == str(ended_lot.id)
    assert body["lot"]["title"] == "Dom Casmurro"
    assert body["lot"]["authors"] == ["Machado de Assis"]
    assert body["lot"]["bid_count"] == 2
    assert body["status"] == "INTEGRO"
    assert len(body["checks"]) == 7
    assert body["checked_at"] is not None
    assert [bid["bidder_alias"] for bid in body["bids"]] == [bidder.public_alias, other_bidder.public_alias]
    assert set(body["bids"][0]) == {
        "sequence", "bidder_alias", "amount", "created_at", "prev_hash", "hash", "ok",
    }
    content = response.content.decode()
    for person in (bidder, other_bidder):
        assert person.email not in content
        assert person.name not in content
        assert str(person.id) not in content


def test_unknown_lot_answers_404(api_client, db):
    assert api_client.get(audit_url(uuid.uuid4())).status_code == 404


def test_audit_settles_a_lot_that_already_ended(api_client, ended_lot):
    body = api_client.get(audit_url(ended_lot.id)).json()

    ended_lot.refresh_from_db()
    assert ended_lot.status == Lot.Status.CLOSED
    assert body["lot"]["phase"] == "CLOSED"
    assert body["lot"]["closed_at"] is not None
    receipt = next(check for check in body["checks"] if check["key"] == "receipt")
    assert receipt["status"] == "ok"


def test_cancelled_lot_can_be_audited(api_client, make_lot):
    lot = make_lot()
    Lot.objects.filter(id=lot.id).update(status=Lot.Status.CANCELLED)

    response = api_client.get(audit_url(lot.id))

    assert response.status_code == 200
    assert response.json()["lot"]["phase"] == "CANCELLED"
    assert response.json()["status"] == "INTEGRO"


def test_public_key_is_published(api_client, db):
    response = api_client.get(reverse("audit-public-key"))

    assert response.status_code == 200
    assert response.json()["algorithm"] == "Ed25519"
    assert response.json()["public_key"].startswith("ed25519:")


def test_31st_request_in_a_minute_answers_429(api_client, make_lot):
    url = audit_url(make_lot().id)

    for _ in range(30):
        assert api_client.get(url).status_code == 200
    assert api_client.get(url).status_code == 429
