PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
READY := $(VENV)/.ready

.DEFAULT_GOAL := build

.PHONY: setup build test install uninstall clean distclean

setup: $(READY)

$(READY): requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --disable-pip-version-check -r requirements.txt
	touch $(READY)

build: setup
	$(VENV_PYTHON) scripts/build_font.py

test: build
	$(VENV_PYTHON) -m unittest discover -s tests -v

install: build
	$(VENV_PYTHON) scripts/install_font.py

uninstall:
	$(PYTHON) scripts/install_font.py --remove

clean:
	rm -rf dist

distclean: clean
	rm -rf .venv

