"""Lances ao mesmo tempo: as travas deixam passar só o que as regras permitem."""

import threading

import pytest
from django.db import connections

from apps.accounts.models import User
from apps.auctions.models import Lot
from apps.wallet.services import deposit
from core.exceptions import BusinessRuleError

from .models import Bid
from .services import place_bid

ACCEPTED = "ACCEPTED"


def run_at_the_same_time(*calls):
    """Roda cada função numa thread, todas começando juntas, e devolve o resultado de cada uma."""
    barrier = threading.Barrier(len(calls), timeout=10)
    results = [None] * len(calls)

    def worker(index, call):
        try:
            barrier.wait()
            call()
            results[index] = ACCEPTED
        except BusinessRuleError as error:
            results[index] = error.code
        except Exception as error:  # qualquer outro erro aparece no resultado do teste
            results[index] = repr(error)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker, args=(i, call)) for i, call in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def create_bidders(count, balance):
    bidders = []
    for number in range(count):
        bidder = User.objects.create_user(
            email=f"concorrente{number}@exemplo.com",
            password="SenhaSegura123!",
            name=f"Concorrente {number}",
            role=User.Role.BIDDER,
        )
        deposit(bidder, balance)
        bidders.append(bidder)
    return bidders


@pytest.mark.django_db(transaction=True)
def test_ten_simultaneous_bids_of_the_same_value_accept_only_one(make_lot):
    lot = make_lot()
    bidders = create_bidders(10, 100_000)

    results = run_at_the_same_time(
        *[lambda bidder=bidder: place_bid(lot.id, bidder, 10_000) for bidder in bidders]
    )

    assert results.count(ACCEPTED) == 1
    assert results.count("BELOW_MINIMUM") == 9
    lot.refresh_from_db()
    assert lot.bid_count == 1
    assert Bid.objects.filter(lot=lot).count() == 1


@pytest.mark.django_db(transaction=True)
def test_same_bidder_cannot_spend_the_same_money_in_two_lots(make_lot):
    first, second = make_lot(), make_lot()
    (bidder,) = create_bidders(1, 100_000)

    results = run_at_the_same_time(
        lambda: place_bid(first.id, bidder, 80_000),
        lambda: place_bid(second.id, bidder, 80_000),
    )

    assert sorted(results) == [ACCEPTED, "INSUFFICIENT_BALANCE"]
    assert Lot.objects.filter(leader=bidder).count() == 1
