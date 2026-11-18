from dataclasses import dataclass
from uuid import UUID

from pantry_scanner.domain.enums import MatchConfidence, MatchSource, Unit
from pantry_scanner.domain.models import Ingredient, IngredientAlias, Match
from pantry_scanner.domain.units import unit_family
from pantry_scanner.matching.normalize import normalize, similarity

ACCOUNT_FUZZY_THRESHOLD = 85
CATALOG_FUZZY_THRESHOLD = 88
HIGH_CONFIDENCE_THRESHOLD = 95


@dataclass(frozen=True)
class Candidate:
    ingredient: Ingredient
    source: MatchSource
    score: int


def _unit_compatible(candidate: Ingredient, detected_unit: Unit | None) -> bool:
    if detected_unit is None or candidate.unit is None:
        return True
    if unit_family(candidate.unit) != unit_family(detected_unit):
        return False
    if unit_family(detected_unit) == "discrete":
        return candidate.unit == detected_unit
    return True


def _as_match(candidate: Ingredient, source: MatchSource, confidence: MatchConfidence) -> Match:
    return Match(
        source=source,
        ingredient_id=candidate.id if source == MatchSource.ACCOUNT else None,
        catalog_ingredient_id=candidate.id if source == MatchSource.CATALOG else None,
        name=candidate.name,
        unit=candidate.unit,
        confidence=confidence,
    )


def _find_candidate(
    name: str,
    detected_unit: Unit | None,
    candidates: list[Ingredient],
    source: MatchSource,
    threshold: int,
) -> Match | None:
    active = [
        ingredient
        for ingredient in candidates
        if source != MatchSource.ACCOUNT or ingredient.archived_at is None
    ]
    exact = [item for item in active if normalize(item.normalized_name) == name]
    if exact:
        chosen = max(exact, key=lambda item: _unit_compatible(item, detected_unit))
        return _as_match(chosen, source, MatchConfidence.HIGH)
    ranked = [
        (similarity(name, item.normalized_name), _unit_compatible(item, detected_unit), item)
        for item in active
    ]
    qualified = [entry for entry in ranked if entry[0] >= threshold]
    if not qualified:
        return None
    score, _, chosen = max(qualified, key=lambda entry: (entry[1], entry[0]))
    confidence = (
        MatchConfidence.HIGH if score >= HIGH_CONFIDENCE_THRESHOLD else MatchConfidence.MEDIUM
    )
    return _as_match(chosen, source, confidence)


def match_ingredient(
    detected_name: str,
    detected_unit: Unit | None,
    account_id: UUID,
    account_ingredients: list[Ingredient],
    catalog_ingredients: list[Ingredient],
    aliases: list[IngredientAlias],
) -> Match:
    normalized = normalize(detected_name)
    for alias in aliases:
        if alias.account_id != account_id or normalize(alias.normalized_alias) != normalized:
            continue
        if alias.ingredient_source == MatchSource.ACCOUNT:
            candidate = next(
                (item for item in account_ingredients if item.id == alias.ingredient_id), None
            )
        else:
            candidate = next(
                (item for item in catalog_ingredients if item.id == alias.catalog_ingredient_id),
                None,
            )
        if candidate is not None and (
            alias.ingredient_source != MatchSource.ACCOUNT or candidate.archived_at is None
        ):
            return _as_match(candidate, alias.ingredient_source, MatchConfidence.HIGH)

    account_match = _find_candidate(
        normalized, detected_unit, account_ingredients, MatchSource.ACCOUNT, ACCOUNT_FUZZY_THRESHOLD
    )
    if account_match is not None:
        return account_match
    catalog_match = _find_candidate(
        normalized, detected_unit, catalog_ingredients, MatchSource.CATALOG, CATALOG_FUZZY_THRESHOLD
    )
    return catalog_match or Match()
