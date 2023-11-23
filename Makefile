SHELL := bash
PYTHON_VENV = source .venv/bin/activate &&
PIP_CONFIG_FILE := ./pip.conf

.venv:
	python -m venv .venv
.PHONY: .venv

install: .venv
	$(PYTHON_VENV) pip install -e .[build,dev,docs]
.PHONY: install

install-lock: .venv
	$(PYTHON_VENV) pip install -r requirements-dev.txt
.PHONY: install-lock

install-lock-ci: .venv
	$(PYTHON_VENV) pip install -r requirements-dev.txt --trusted-host=nexus.team-z.dev --index-url=https://nexus.team-z.dev/repository/pypi-proxy/simple
.PHONY: install-lock-ci

install-build-lock: .venv
	$(PYTHON_VENV) pip install -r requirements-build.txt
.PHONY: install-build-lock

black:
	$(PYTHON_VENV) black ./trader ./notebooks
.PHONY: black

isort:
	$(PYTHON_VENV) isort ./trader
.PHONY: isort

pretty: black isort
.PHONY: pretty

black_check:
	$(PYTHON_VENV) black ./trader ./notebooks --check
.PHONY: black_check

isort_check:
	$(PYTHON_VENV) isort --check-only ./trader
.PHONY: isort_check

pyright_check:
	$(PYTHON_VENV) pyright --stats
.PHONY: pyright_check

lint: black_check isort_check pyright_check
.PHONY: lint

test:
	$(PYTHON_VENV) pytest trader/tests -v --cov=./trader --cov-report term-missing --cov-config=.coveragerc
.PHONY: test

test-verbose:
	$(PYTHON_VENV) pytest trader/tests -s -v --cov=./trader --cov-report term-missing --cov-config=.coveragerc
.PHONY: test-verbose

migrations:
	$(PYTHON_VENV) python -m alembic revision --autogenerate || true
	$(PYTHON_VENV) python -m alembic upgrade head
.PHONY: migrations

pex: .venv
	$(PYTHON_VENV) pex . \
		--python-shebang="#!/usr/bin/env python3" \
		--console-script trader -v -o trader.pex \
		--disable-cache
	chmod +x ./trader.pex
.PHONY: pex

pex_debug: pex
	rm -Rf temp || true
	mkdir temp
	cp trader.pex temp/trader.pex
	cd temp && unzip trader.pex
.PHONY: pex_debug

clean:
	rm -Rf temp || true
	rm -Rf dist || true
	rm -Rf .venv || true
.PHONY: clean

jupyter:
	$(PYTHON_VENV) jupyter lab
.PHONY: jupyter

gen-lockfiles: .venv
	# allow-unsafe required for build tools apparently: https://stackoverflow.com/a/58864335
	$(PYTHON_VENV) pip-compile \
		--resolver=backtracking \
		--generate-hashes \
		--allow-unsafe \
		--extra=build \
		-o requirements-build.txt -v
	$(PYTHON_VENV) pip-compile \
		--resolver=backtracking \
		--generate-hashes \
		--allow-unsafe \
		--extra=dev \
		-o requirements-dev.txt -v
	$(PYTHON_VENV) pip-compile \
		--resolver=backtracking \
		--generate-hashes \
		--allow-unsafe \
		--extra=docs \
		-o requirements-docs.txt -v
.PHONY: gen-lockfiles

build:
	docker build -f Dockerfile -t trader . 
.PHONY: build

start-docs:
	$(PYTHON_VENV) python -m mkdocs serve --dev-addr=0.0.0.0:8000
.PHONY: start-docs
