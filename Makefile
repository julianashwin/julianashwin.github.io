PYTHON := .venv/bin/python3

preview: cv
	QUARTO_PYTHON=$(PYTHON) quarto preview --no-cache

render: cv
	QUARTO_PYTHON=$(PYTHON) quarto render --no-cache

cv:
	$(PYTHON) scripts/build_cv.py

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

.PHONY: preview render cv install
