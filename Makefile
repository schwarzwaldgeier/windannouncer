# Default target
default: help

# Always run these targets even if a file with the same name exists
.PHONY: help install run venv

## help: show this help message
help: Makefile
	@echo "Usage: make <target>\n"
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/ /'

## venv: create virtual environment (.venv)
venv:
	python3 -m venv .venv

## install: install required packages inside venv
install: venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

## run: run listener
run:
	. .venv/bin/activate && python main.py


## clean: remove cache files
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
