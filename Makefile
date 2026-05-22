PYTHON := .venv/bin/python3

preview:
	QUARTO_PYTHON=$(PYTHON) quarto preview --no-cache

render:
	QUARTO_PYTHON=$(PYTHON) quarto render --no-cache

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

.PHONY: preview render install
