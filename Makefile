PY ?= .venv/bin/python

.PHONY: all venv fetch build test estimate figures tables paper-assets paper clean

# fetch -> build -> (sanity tests) -> estimate -> figures -> tables -> paper assets (numbers, tables, figures)
all: build test estimate figures tables paper-assets

venv:
	python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt

fetch:
	$(PY) -m src.pipeline fetch

build:
	$(PY) -m src.pipeline build

test:
	$(PY) -m pytest -q -s tests

estimate:
	$(PY) -m src.pipeline estimate

figures:
	$(PY) -m src.pipeline figures

tables:
	$(PY) -m src.pipeline tables

paper-assets:
	$(PY) -m src.pipeline paper

# Build paper/paper.pdf (pinned Tectonic; needs network on first run for the binary and TeX bundle).
paper: paper-assets
	bash paper/build.sh

# Re-download all raw data (new vintage), then rebuild everything.
refresh:
	$(PY) -m src.pipeline build --refresh && $(MAKE) test estimate figures tables paper-assets

clean:
	rm -rf data/processed/*.parquet output/figures/*.png output/figures/*.svg output/tables/*
