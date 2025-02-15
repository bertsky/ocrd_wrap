PYTHON = python3
PIP = pip3
PYTHONIOENCODING=utf8

DOCKER_BASE_IMAGE = docker.io/ocrd/core:v3.0.3
DOCKER_TAG = ocrd/wrap

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
	@echo "    docker       Build a Docker image $(DOCKER_TAG) from $(DOCKER_BASE_IMAGE)"

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

docker:
	docker build \
	--build-arg DOCKER_BASE_IMAGE=$(DOCKER_BASE_IMAGE) \
	--build-arg VCS_REF=$$(git rev-parse --short HEAD) \
	--build-arg BUILD_DATE=$$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t $(DOCKER_TAG) .

.PHONY: help deps deps-test install install-dev test docker
