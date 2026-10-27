"""Testes do ticket do WebSocket."""

from django.urls import reverse

from . import tickets


def test_ticket_requires_login(api_client, db):
    assert api_client.post(reverse("auth-ws-ticket")).status_code == 403


def test_logged_user_gets_a_ticket_that_works_once(api_client, bidder):
    api_client.force_login(bidder)

    body = api_client.post(reverse("auth-ws-ticket")).json()

    assert body["expires_in"] == 30
    assert tickets.redeem_ticket(body["ticket"]) == str(bidder.id)
    assert tickets.redeem_ticket(body["ticket"]) is None


def test_expired_ticket_is_worthless(bidder, monkeypatch):
    monkeypatch.setattr(tickets, "TICKET_SECONDS", 0)

    token = tickets.issue_ticket(bidder)

    assert tickets.redeem_ticket(token) is None


def test_made_up_ticket_is_worthless(db):
    assert tickets.redeem_ticket("ticket-inventado") is None
    assert tickets.redeem_ticket(None) is None