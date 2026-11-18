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
	sam build --template-file infra/template.yaml --use-container

deploy:
	@if [ "$(STAGE)" != "beta" ] && [ "$(STAGE)" != "prod" ]; then echo "STAGE must be beta or prod"; exit 2; fi
	sam deploy --template-file .aws-sam/build/template.yaml --config-env $(STAGE) --no-confirm-changeset --no-fail-on-empty-changeset
