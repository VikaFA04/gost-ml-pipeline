# Pre-PR gate. Default interpreter is python3 (this repo's macOS host has
# no plain `python`); override with `make PYTHON=python regression-gate`
# if your environment provides `python -m src.main audit-regression`.
PYTHON ?= python3
POSITIVE_DIR ?= positive_examples
NEGATIVE_DIR ?= negative_examples
PROFILE_ID ?= gost_7_32_2017
SUBSET_LIMIT ?= 4

.PHONY: regression-gate
regression-gate:
	$(PYTHON) -m src.main audit-regression \
		--positive-dir $(POSITIVE_DIR) \
		--negative-dir $(NEGATIVE_DIR) \
		--profile-id $(PROFILE_ID) \
		--limit $(SUBSET_LIMIT)
	$(PYTHON) -m pytest -q \
		tests/test_negative_corpus_diff_rate.py \
		tests/test_positive_docx_regression.py \
		tests/test_rules_quality_acceptance.py \
		tests/test_format_regression_audit.py \
		tests/test_profile_quality_acceptance.py \
		tests/test_methodical_extractor.py

.PHONY: compare-classical-acceptance
compare-classical-acceptance:
	$(PYTHON) -m src.main compare-classical \
		--output-dir results/reports/classical_zoo_$$(date +%Y%m%d_%H%M%S)/
	$(PYTHON) -m pytest tests/test_phase_8_sc2_acceptance.py -v
