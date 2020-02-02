.PHONY: requirements
requirements:
	pip-compile --generate-hashes --output-file=requirements.txt requirements.in

.PHONY: requirements-dev
requirements-dev:
	pip-compile --generate-hashes --output-file=requirements-dev.txt requirements-dev.in
