from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pantry_scanner.domain.enums import (
    IngredientCategory,
    MatchConfidence,
    MatchSource,
    QuantityBasis,
    ScanStatus,
    Unit,
)
from pantry_scanner.domain.models import Match, Quantity, ScanItem, ScanMessage, ScanResult
from pantry_scanner.domain.units import convert_amount, unit_family


def test_frozen_scan_message_contract() -> None:
    message = ScanMessage.model_validate(
        {
            "v": 1,
            "scan_id": "11111111-2222-4333-8444-555555555555",
            "account_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        }
    )
    assert str(message.scan_id) == "11111111-2222-4333-8444-555555555555"
    with pytest.raises(ValidationError):
        ScanMessage.model_validate({"v": 2, "scan_id": str(uuid4()), "account_id": str(uuid4())})
    with pytest.raises(ValidationError):
        ScanMessage.model_validate(
            {
                "v": 1,
                "scan_id": str(uuid4()),
                "account_id": str(uuid4()),
                "extra": True,
            }
        )


def test_result_model_serializes_contract_values() -> None:
    result = ScanResult(
        items=[
            ScanItem(
                detected_name="milk",
                match=Match(source=MatchSource.ACCOUNT, confidence=MatchConfidence.HIGH),
                suggested_category=IngredientCategory.DAIRY,
                quantity=Quantity(
                    amount=Decimal("2"),
                    unit=Unit.EACH,
                    basis=QuantityBasis.COUNT,
                    is_lower_bound=True,
                ),
            )
        ],
        warnings=["partly hidden"],
    )
    item = result.model_dump(mode="json")["items"][0]
    assert item["quantity"]["is_lower_bound"] is True
    assert item["match"]["source"] == "ACCOUNT"
    assert item["quantity"]["unit"] == "EACH"


def test_all_contract_enums_are_present() -> None:
    assert set(ScanStatus) == {
        ScanStatus.AWAITING_UPLOAD,
        ScanStatus.QUEUED,
        ScanStatus.ANALYSING,
        ScanStatus.COMPLETED,
        ScanStatus.FAILED,
        ScanStatus.CANCELLED,
        ScanStatus.CONFIRMED,
        ScanStatus.EXPIRED,
    }


def test_unit_conversion_uses_decimal_factors() -> None:
    assert convert_amount(Decimal("1"), Unit.OUNCES, Unit.GRAMS) == Decimal("28.3495")
    assert convert_amount(Decimal("1"), Unit.CUP, Unit.MILLILITERS) == Decimal("236.588")
    assert unit_family(Unit.SLICE) == "discrete"
    with pytest.raises(ValueError):
        convert_amount(Decimal("1"), Unit.SLICE, Unit.EACH)
