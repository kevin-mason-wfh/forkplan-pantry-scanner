.PHONY: install check build deploy

STAGE ?= beta

install:
	uv sync --all-extras --dev

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run pytest

build:
	sam build --use-container

deploy:
	@if [ "$(STAGE)" != "beta" ] && [ "$(STAGE)" != "prod" ]; then echo "STAGE must be beta or prod"; exit 2; fi
	sam deploy --config-env $(STAGE) --no-confirm-changeset --no-fail-on-empty-changeset
