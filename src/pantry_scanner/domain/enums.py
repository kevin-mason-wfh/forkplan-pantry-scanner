from enum import StrEnum


class ScanStatus(StrEnum):
    AWAITING_UPLOAD = "AWAITING_UPLOAD"
    QUEUED = "QUEUED"
    ANALYSING = "ANALYSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"


class Unit(StrEnum):
    GRAMS = "GRAMS"
    KILOGRAMS = "KILOGRAMS"
    OUNCES = "OUNCES"
    POUNDS = "POUNDS"
    MILLILITERS = "MILLILITERS"
    LITERS = "LITERS"
    TEASPOON = "TEASPOON"
    TABLESPOON = "TABLESPOON"
    CUP = "CUP"
    FLUID_OUNCE = "FLUID_OUNCE"
    EACH = "EACH"
    SLICE = "SLICE"
    RASHER = "RASHER"


class IngredientCategory(StrEnum):
    MEAT = "MEAT"
    SEAFOOD = "SEAFOOD"
    DAIRY = "DAIRY"
    EGGS = "EGGS"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    BREAD_BAKERY = "BREAD_BAKERY"
    PASTA = "PASTA"
    RICE_GRAINS = "RICE_GRAINS"
    CEREAL = "CEREAL"
    BEANS_LEGUMES = "BEANS_LEGUMES"
    PLANT_PROTEIN = "PLANT_PROTEIN"
    NUT_SEED = "NUT_SEED"
    HERB_SPICE = "HERB_SPICE"
    OIL_FAT = "OIL_FAT"
    SAUCE = "SAUCE"
    CONDIMENT = "CONDIMENT"
    BAKING_COOKING = "BAKING_COOKING"
    SWEETS_SNACKS = "SWEETS_SNACKS"
    BEVERAGE = "BEVERAGE"
    OTHER = "OTHER"


class MatchConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class MatchSource(StrEnum):
    ACCOUNT = "ACCOUNT"
    CATALOG = "CATALOG"


class QuantityBasis(StrEnum):
    COUNT = "count"
    LABEL = "label"
    VISUAL = "visual"


class ScanErrorCode(StrEnum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_OUTPUT = "invalid_output"
    TIMEOUT = "timeout"
    NO_IMAGES_USABLE = "no_images_usable"
    INTERNAL_ERROR = "internal_error"
