from decimal import Decimal

from pantry_scanner.domain.enums import Unit

MASS_FACTORS: dict[Unit, Decimal] = {
    Unit.GRAMS: Decimal("1"),
    Unit.KILOGRAMS: Decimal("1000"),
    Unit.OUNCES: Decimal("28.3495"),
    Unit.POUNDS: Decimal("453.592"),
}
VOLUME_FACTORS: dict[Unit, Decimal] = {
    Unit.MILLILITERS: Decimal("1"),
    Unit.LITERS: Decimal("1000"),
    Unit.TEASPOON: Decimal("4.92892"),
    Unit.TABLESPOON: Decimal("14.7868"),
    Unit.CUP: Decimal("236.588"),
    Unit.FLUID_OUNCE: Decimal("29.5735"),
}
DISCRETE_UNITS = {Unit.EACH, Unit.SLICE, Unit.RASHER}


def unit_family(unit: Unit | None) -> str | None:
    if unit is None:
        return None
    if unit in MASS_FACTORS:
        return "mass"
    if unit in VOLUME_FACTORS:
        return "volume"
    if unit in DISCRETE_UNITS:
        return "discrete"
    return None


def convert_amount(amount: Decimal, source: Unit, target: Unit) -> Decimal:
    if source == target:
        return amount
    if source in MASS_FACTORS and target in MASS_FACTORS:
        return amount * MASS_FACTORS[source] / MASS_FACTORS[target]
    if source in VOLUME_FACTORS and target in VOLUME_FACTORS:
        return amount * VOLUME_FACTORS[source] / VOLUME_FACTORS[target]
    raise ValueError(f"Cannot convert {source} to {target}")
