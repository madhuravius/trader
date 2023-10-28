SHELL := bash
PYTHON_VENV = source .venv/bin/activate &&

.venv:
	python -m venv .venv
.PHONY: .venv

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
	$(PYTHON_VENV) pyright .
.PHONY: pyright_check

lint: black_check isort_check pyright_check
.PHONY: lint

migrations:
	$(PYTHON_VENV) python -m alembic revision --autogenerate -m "migration $(date +%s)"
	$(PYTHON_VENV) python -m alembic upgrade head
.PHONY: migrations
