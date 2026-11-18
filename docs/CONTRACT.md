# Frozen integration contract

The separate API project owns the schema, uploads, and mobile API. These names
are integration boundaries and must not be changed by this worker.

## Queue and object keys

The SQS body is `{"v": 1, "scan_id": "<uuid>", "account_id": "<uuid>"}`.
Objects are stored under
`scan-temp/{account_id}/{scan_id}/{index}.jpg` in `SCAN_BUCKET`; the API
persists their keys in `pantry_scans.image_keys`.

## Statuses and errors

Statuses are `AWAITING_UPLOAD`, `QUEUED`, `ANALYSING`, `COMPLETED`, `FAILED`,
`CANCELLED`, `CONFIRMED`, and `EXPIRED`. Error codes are `provider_unavailable`,
`invalid_output`, `timeout`, `no_images_usable`, and `internal_error`.

## Database

`pantry_scans` contains `id`, `account_id`, `user_id`, `pantry_id`, `location`,
`status`, `image_count`, `image_keys`, `result`, `warnings`, `error_code`,
`provider`, `model`, `prompt_version`, `created_at`, `started_at`,
`completed_at`, and `expires_at`. The worker writes only the scan row. The API
adds its `current` field at read time.

Ingredients are read from `ingredients(id, account_id, name, normalized_name,
unit, size, category, archived_at)` and published
`catalog_ingredients(id, name, normalized_name, unit, size, category, status)`.
Aliases are read from `ingredient_aliases(account_id, normalized_alias,
ingredient_source, ingredient_id, catalog_ingredient_id)`. Feedback rows in
`pantry_scan_feedback` older than 12 months are removed by the sweeper.

## Enums and result schema

Units: `GRAMS`, `KILOGRAMS`, `OUNCES`, `POUNDS`, `MILLILITERS`, `LITERS`,
`TEASPOON`, `TABLESPOON`, `CUP`, `FLUID_OUNCE`, `EACH`, `SLICE`, `RASHER`.

Categories: `MEAT`, `SEAFOOD`, `DAIRY`, `EGGS`, `VEGETABLE`, `FRUIT`,
`BREAD_BAKERY`, `PASTA`, `RICE_GRAINS`, `CEREAL`, `BEANS_LEGUMES`,
`PLANT_PROTEIN`, `NUT_SEED`, `HERB_SPICE`, `OIL_FAT`, `SAUCE`, `CONDIMENT`,
`BAKING_COOKING`, `SWEETS_SNACKS`, `BEVERAGE`, `OTHER`.

`pantry_scans.result` is `{"items": [Item], "warnings": [string]}`. Each item
contains `temp_id` (UUID), `detected_name`, `match`, `suggested_category`,
`quantity`, and nullable `notes`. `match` contains `source` (`ACCOUNT`,
`CATALOG`, or null), nullable account/catalog IDs, nullable matched name and
unit, and confidence (`high`, `medium`, `low`, `none`). `quantity` contains
nullable amount and unit, nullable basis (`count`, `label`, `visual`),
confidence, `is_lower_bound`, and `unit_mismatch`. The corresponding strict
Pydantic definitions are in `src/pantry_scanner/domain/models.py`.
