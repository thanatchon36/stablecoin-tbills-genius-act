PY ?= .venv/bin/python

.PHONY: all venv fetch build test estimate figures tables clean

# fetch -> build -> (sanity tests) -> estimate -> figures -> tables
all: build test estimate figures tables

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

# Re-download all raw data (new vintage), then rebuild everything.
refresh:
	$(PY) -m src.pipeline build --refresh && $(MAKE) test estimate figures tables

clean:
	rm -rf data/processed/*.parquet output/figures/*.png output/figures/*.svg output/tables/*
