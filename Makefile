export

SHELL = /bin/bash
PYTHON = python3
PIP = pip3
LOG_LEVEL = INFO
PYTHONIOENCODING=utf8
SHARE_DIR=~/.local/share

deps-dev:
	$(PIP) install -r requirements-dev.txt

deps:
	$(PIP) install -r requirements.txt

install:
	$(PIP) install -e .

clean-build: pyclean
	rm -Rf build dist *.egg-info

pyclean:
	rm -f **/*.pyc
	rm -rf .pytest_cache
	rm -rf .mypy_cache/

build: clean-build
	$(PYTHON) -m build

testpypi: clean-build build
	twine upload --repository testpypi ./dist/flipper[_-]raw[_-]rfid*.{tar.gz,whl}

pypi: clean-build build
	twine upload ./dist/flipper[_-]raw[_-]rfid*.{tar.gz,whl}

flake8: deps-dev
	$(PYTHON) -m flake8 flipper_raw_rfid tests

mypy: deps-dev
	$(PYTHON) -m mypy --show-error-codes  -p flipper_raw_rfid

codespell: deps-dev
	codespell

test: deps-dev
	$(PYTHON) -m xmlrunner discover -v -s tests --output-file $(CURDIR)/unittest.xml

ci: flake8 mypy test codespell


.PHONY: assets-clean
# Remove symlinks in test/assets
assets-clean:
	rm -rf test/assets
