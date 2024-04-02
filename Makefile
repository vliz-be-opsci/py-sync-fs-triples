TEST_PATH = ./tests/
FLAKE8_EXCLUDE = venv,.venv,.eggs,.tox,.git,__pycache__,*.pyc
PROJECT = syncfstriples
AUTHOR = "Flanders Marine Institute, VLIZ vzw"

.PHONY: help build check help init-dev init install lint-fix release startup test-coverage test update
.DEFAULT_GOAL := help

help:  ## Shows this list of available targets and their effect.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean:
	@find . -name '*.pyc' -exec rm --force {} +
	@find . -name '*.pyo' -exec rm --force {} +
	@find . -name '*~' -exec rm --force {} +
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -f *.sqlite
	@rm -rf .cache

startup: ## prepares environment for using poetry (a core dependency for this project)
	@pip install --upgrade pip
	@which poetry >/dev/null || pip install poetry

install:  ## install this package in the current environment
	@poetry install

init: startup install  ## initial prepare of the environment for local execution of the package

init-dev: startup  ## initial prepare of the environment for further development in the package
	@poetry install --with 'tests' --with 'dev' --with 'docs'

test:  ## runs the standard test-suite for the memory-graph implementation
	@poetry run pytest ${TEST_PATH}

test-coverage:  ## runs the standard test-suite for the memory-graph implementation and produces a coverage report
	@poetry run pytest --cov=$(PROJECT) ${TEST_PATH} --cov-report term-missing

check:  ## performs linting on the python code
	@poetry run black --check --diff .
	@poetry run isort --check --diff .
	@poetry run flake8 . --exclude ${FLAKE8_EXCLUDE} --ignore=E501,E201,E203,E202,W503

lint-fix:  ## fixes code according to the lint suggestions
	@poetry run black .
	@poetry run isort .

update:  ## updates dependencies
	@poetry update

build: update check test docs  ## builds the package
	@poetry build

release: build  ## releases the package
	@poetry release