from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.api.v1.routes import decode_cursor
from backend.api.v1.schemas import CartItemIn, CityIn, JournalLineIn
from backend.domain.rules import BusinessError, balanced, money, transition
from backend.persistence.registry import metadata


def test_balanced_journal_cannot_hide_cross_currency_imbalance():
    balanced([("INR", Decimal("10")), ("INR", Decimal("-10"))])
    with pytest.raises(BusinessError):
        balanced([("INR", Decimal("10")), ("USD", Decimal("-10"))])


@pytest.mark.parametrize(
    "lines",
    [
        [],
        [("INR", Decimal("0")), ("INR", Decimal("0"))],
        [("INR", Decimal("NaN")), ("INR", Decimal("-1"))],
    ],
)
def test_invalid_journals(lines):
    with pytest.raises(BusinessError):
        balanced(lines)


def test_bankers_rounding_and_currency_scale():
    assert money(Decimal("1.005"), 2) == Decimal("1.00")
    assert money(Decimal("1.015"), 2) == Decimal("1.02")
    assert money(Decimal("4.5"), 0) == Decimal("4")
    assert money(Decimal("1.2345"), 3) == Decimal("1.234")


def test_transition_rules_do_not_allow_direct_delivery():
    transition("merchant", "pending", "accepted")
    transition("delivery", "picked_up", "delivered")
    with pytest.raises(BusinessError):
        transition("delivery", "unassigned", "delivered")


def test_request_boundaries():
    with pytest.raises(ValidationError):
        JournalLineIn(account_id=uuid4(), amount="1.00001")
    with pytest.raises(ValidationError):
        CityIn(name="City", country_id=uuid4(), timezone="not/a/timezone")
    assert (
        CityIn(name="City", country_id=uuid4(), timezone="Asia/Kolkata").timezone == "Asia/Kolkata"
    )
    with pytest.raises(ValidationError):
        CartItemIn(branch_id=uuid4(), variant_id=uuid4(), window_id=uuid4(), quantity=-1)


def test_opaque_cursor_rejects_arbitrary_input():
    with pytest.raises(BusinessError):
        decode_cursor("invalid-cursor")


def test_full_metadata_has_real_relationships_and_no_float_money():
    assert len(metadata.tables) >= 240
    assert len({table.schema for table in metadata.tables.values()}) == 14
    for table in metadata.tables.values():
        for column in table.columns:
            assert str(column.type) not in {"FLOAT", "DOUBLE PRECISION", "MONEY"}
            for foreign in column.foreign_keys:
                assert foreign.column is not None
                assert foreign.ondelete == "RESTRICT"
