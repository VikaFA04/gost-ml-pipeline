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

# ---------------------------------------------------------------------------
# Phase 8: Milestone acceptance gate
# D-A-01: single command; exit 0 = PASS; non-zero halts chain at first failure.
# D-A-03: each SC also runnable independently for triage.
# D-E-03: chain order SC-3 -> SC-1 -> SC-2 -> SC-4 (cheapest fail-fast first).
# ---------------------------------------------------------------------------

.PHONY: milestone-acceptance-sc3
milestone-acceptance-sc3:
	$(MAKE) regression-gate

.PHONY: milestone-acceptance-sc1
milestone-acceptance-sc1:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc1.py -v

.PHONY: milestone-acceptance-sc2
milestone-acceptance-sc2:
	$(MAKE) compare-classical-acceptance
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc2_after_rules.py -v

.PHONY: milestone-acceptance-sc4
milestone-acceptance-sc4:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc4.py -v

.PHONY: milestone-acceptance
milestone-acceptance: milestone-acceptance-sc3 milestone-acceptance-sc1 milestone-acceptance-sc2 milestone-acceptance-sc4

# D-A-04: fast CI tier — SC-1 fast fixtures + existing zoo + regression + Streamlit smoke.
.PHONY: milestone-smoke
milestone-smoke:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc1.py -v -m "not slow"
	$(MAKE) compare-classical-acceptance
	$(MAKE) regression-gate
	$(PYTHON) -m pytest tests/test_streamlit_smoke.py -v
