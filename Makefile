SHELL := bash
PYTHON_VENV = source .venv/bin/activate &&

.venv:
	python -m venv .venv
.PHONY: .venv

ci: .venv
	$(PYTHON_VENV) pip install -r requirements.txt
.PHONY: ci

install: .venv
	$(PYTHON_VENV) pip install \
		-e .[test]
.PHONY: install

black:
	$(PYTHON_VENV) black ./trader
.PHONY: black

isort:
	$(PYTHON_VENV) isort ./trader
.PHONY: isort

pretty: black isort
.PHONY: pretty

black_check:
	$(PYTHON_VENV) black ./trader --check
.PHONY: black_check

isort_check:
	$(PYTHON_VENV) isort --check-only ./trader
.PHONY: isort_check

pyright_check:
	$(PYTHON_VENV) pyright --stats
.PHONY: pyright_check

lint: black_check isort_check pyright_check
.PHONY: lint

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

gen-lockfile: .venv
	$(PYTHON_VENV) pip-compile \
		--resolver=backtracking \
		--generate-hashes \
		-o requirements.txt -v
.PHONY: gen-lockfile
