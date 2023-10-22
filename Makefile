SHELL := bash
PYTHON_VENV = source .venv/bin/activate &&

.venv:
	python -m venv .venv
.PHONY: .venv

install: .venv
	$(PYTHON_VENV) pip install \
		-e .[test]
.PHONY: install

