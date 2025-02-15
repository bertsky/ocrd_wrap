PYTHON = python3
PIP = pip3
PYTHONIOENCODING=utf8

help:
	@echo
	@echo "  Targets"
	@echo
	@echo "    deps         Install only Python deps via pip"
	@echo "    deps-test    Install testing deps via pip"
	@echo "    install      Install full Python package via pip"
	@echo "    install-dev  Install in editable mode"
	@echo "    build        Build source and binary distribution"
	@echo "    repo/assets  Clone OCR-D/assets to ./repo/assets"
	@echo "    tests/assets Setup test assets"

# Install Python deps via pip
deps:
	$(PIP) install -r requirements.txt

# Install testing deps via pip
deps-test:
	$(PIP) install -r requirements_test.txt

# Install Python package via pip
install:
	$(PIP) install .

install-dev:
	$(PIP) install -e .

build:
	$(PIP) install build
	$(PYTHON) -m build .

# Run test
test: tests/assets
	$(PYTHON) -m pytest  tests --durations=0 $(PYTEST_ARGS)

#
# Assets
#

# Update OCR-D/assets submodule
.PHONY: repos always-update tests/assets
repo/assets: always-update
	git submodule sync --recursive $@
	if git submodule status --recursive $@ | grep -qv '^ '; then \
		git submodule update --init --recursive $@ && \
		touch $@; \
	fi


# Setup test assets
tests/assets: repo/assets
	mkdir -p tests/assets
	cp -a repo/assets/data/* tests/assets

.PHONY: help deps deps-test install install-dev test
