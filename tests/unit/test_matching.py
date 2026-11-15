from tests.conftest import ACCOUNT_ID, INGREDIENT_ID

from pantry_scanner.domain.enums import IngredientCategory, MatchConfidence, MatchSource, Unit
from pantry_scanner.domain.models import Ingredient, IngredientAlias
from pantry_scanner.matching.matcher import (
    ACCOUNT_FUZZY_THRESHOLD,
    CATALOG_FUZZY_THRESHOLD,
    match_ingredient,
)
from pantry_scanner.matching.normalize import normalize


def ingredient(
    name: str, unit: Unit | None = None, ingredient_id=INGREDIENT_ID, account_id=ACCOUNT_ID
) -> Ingredient:
    return Ingredient(
        id=ingredient_id,
        account_id=account_id,
        name=name,
        normalized_name=normalize(name),
        unit=unit,
        category=IngredientCategory.OTHER,
    )


def test_normalize_accents_punctuation_plural_and_synonyms() -> None:
    assert normalize("Crème fraîche!") == "creme fraiche"
    assert normalize("courgettes") == "zucchini"
    assert normalize("aubergines") == "eggplant"
    assert normalize("coriander") == "cilantro"
    assert normalize("rocket") == "arugula"


def test_match_order_alias_then_account_then_catalog(account_ingredient: Ingredient) -> None:
    catalog = ingredient("Milk", Unit.MILLILITERS, ingredient_id=INGREDIENT_ID)
    account = ingredient("Whole milk", Unit.MILLILITERS)
    alias = IngredientAlias(
        account_id=ACCOUNT_ID,
        normalized_alias="milk",
        ingredient_source=MatchSource.CATALOG,
        catalog_ingredient_id=INGREDIENT_ID,
    )
    match = match_ingredient("milk", Unit.MILLILITERS, ACCOUNT_ID, [account], [catalog], [alias])
    assert match.source == MatchSource.CATALOG
    assert match.confidence == MatchConfidence.HIGH

    match = match_ingredient("whole milk", Unit.MILLILITERS, ACCOUNT_ID, [account], [catalog], [])
    assert match.source == MatchSource.ACCOUNT


def test_fuzzy_thresholds_and_unit_family_preference() -> None:
    wrong_unit = ingredient("milk", Unit.EACH, ingredient_id=INGREDIENT_ID)
    compatible = ingredient("milk", Unit.GRAMS, ingredient_id=INGREDIENT_ID, account_id=ACCOUNT_ID)
    match = match_ingredient(
        "milkk",
        Unit.KILOGRAMS,
        ACCOUNT_ID,
        [wrong_unit, compatible],
        [],
        [],
    )
    assert match.unit == Unit.GRAMS
    assert match.confidence in {MatchConfidence.HIGH, MatchConfidence.MEDIUM}
    assert ACCOUNT_FUZZY_THRESHOLD < 100
    assert CATALOG_FUZZY_THRESHOLD >= ACCOUNT_FUZZY_THRESHOLD


def test_archived_account_ingredient_is_not_matched(account_ingredient: Ingredient) -> None:
    archived = account_ingredient.model_copy(update={"archived_at": "2025-01-01T00:00:00Z"})
    match = match_ingredient("milk", None, ACCOUNT_ID, [archived], [], [])
    assert match.source is None
