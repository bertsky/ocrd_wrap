PYTHON = python3
PIP = pip3
PYTHONIOENCODING=utf8

help:
	@echo
	@echo "  Targets"
	@echo
	@echo "    deps    Install only Python deps via pip"
	@echo "    install Install full Python package via pip"

# Install Python deps via pip
deps:
	$(PIP) install -r requirements.txt

# Install Python package via pip
install:
	$(PIP) install .

.PHONY: help deps install
