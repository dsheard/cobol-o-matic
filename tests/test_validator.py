"""Tests for orchestrator.validator -- deterministic artifact validation."""

from __future__ import annotations

from pathlib import Path

import yaml

from orchestrator.models import ProgramFacts
from orchestrator.validator import (
    _is_table_scaffolding,
    _section_has_content,
    check_capability_completeness,
    cleanup_stray_files,
    compute_coverage_summary,
    validate_business_rules,
    validate_cross_cutting_artifact,
    validate_test_specs_outputs,
)


def _write_artifact(path: Path, frontmatter: dict, body: str) -> None:
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    path.write_text(f"---\n{fm_yaml}\n---\n\n{body}", encoding="utf-8")


class TestSectionHasContent:
    def test_section_with_text(self) -> None:
        body = "## Programs\n\nThere are 5 programs.\n\n## Other\n"
        assert _section_has_content(body, "## Programs") is True

    def test_section_empty(self) -> None:
        body = "## Programs\n\n## Other\n"
        assert _section_has_content(body, "## Programs") is False

    def test_section_with_table_data(self) -> None:
        body = (
            "## Programs\n\n"
            "| Name | Type |\n"
            "| --- | --- |\n"
            "| TESTPROG | batch |\n\n"
            "## Other\n"
        )
        assert _section_has_content(body, "## Programs") is True

    def test_section_with_only_table_scaffold(self) -> None:
        body = (
            "## Programs\n\n"
            "| Name | Type |\n"
            "| --- | --- |\n\n"
            "## Other\n"
        )
        assert _section_has_content(body, "## Programs") is False

    def test_missing_section(self) -> None:
        body = "## Other\n\nContent here.\n"
        assert _section_has_content(body, "## Programs") is False

    def test_section_at_end_of_file(self) -> None:
        body = "## Programs\n\nActual data here.\n"
        assert _section_has_content(body, "## Programs") is True


class TestIsTableScaffolding:
    def test_separator_row(self) -> None:
        assert _is_table_scaffolding("| --- | --- |") is True

    def test_empty_cells(self) -> None:
        assert _is_table_scaffolding("|  |  |") is True

    def test_data_row(self) -> None:
        assert _is_table_scaffolding("| TESTPROG | batch |") is False

    def test_non_table(self) -> None:
        assert _is_table_scaffolding("Some plain text") is False


class TestValidateCrossCutting:
    def test_valid_artifact(self, tmp_path: Path) -> None:
        inv_dir = tmp_path / "inventory"
        inv_dir.mkdir()
        artifact = inv_dir / "programs.md"
        _write_artifact(
            artifact,
            {"type": "inventory", "subtype": "programs"},
            "## Programs\n\n| Name | Type |\n| --- | --- |\n| TESTPROG | batch |\n\n"
            "## Program Type Distribution\n\nbatch: 1\n\n"
            "## Unresolved References\n\nNone found.\n",
        )
        result = validate_cross_cutting_artifact(artifact, "inventory/programs.md")
        assert result.passed

    def test_wrong_frontmatter_repaired(self, tmp_path: Path) -> None:
        inv_dir = tmp_path / "inventory"
        inv_dir.mkdir()
        artifact = inv_dir / "programs.md"
        _write_artifact(
            artifact,
            {"type": "wrong", "subtype": "programs"},
            "## Programs\n\nData here.\n\n"
            "## Program Type Distribution\n\nData here.\n",
        )
        result = validate_cross_cutting_artifact(artifact, "inventory/programs.md")
        assert len(result.frontmatter_repairs) == 1
        assert "type" in result.frontmatter_repairs[0]

        content = artifact.read_text(encoding="utf-8")
        assert "type: inventory" in content

    def test_missing_file(self, tmp_path: Path) -> None:
        result = validate_cross_cutting_artifact(
            tmp_path / "missing.md", "inventory/programs.md"
        )
        assert not result.passed
        assert "FILE_MISSING" in result.incomplete_sections

    def test_unknown_artifact(self, tmp_path: Path) -> None:
        artifact = tmp_path / "custom.md"
        artifact.write_text("# Custom\n\nContent.\n")
        result = validate_cross_cutting_artifact(artifact, "custom.md")
        assert result.passed  # unknown artifacts pass vacuously


class TestValidateBusinessRules:
    def _make_facts(self) -> ProgramFacts:
        return ProgramFacts(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=200,
            program_type="batch",
            copybooks=["COCOM01Y"],
            file_reads=["ACCTFILE"],
            call_targets=["DATEUTIL"],
            transid=None,
        )

    def test_valid_br_artifact(self, tmp_path: Path) -> None:
        br_dir = tmp_path / "business-rules"
        br_dir.mkdir()
        artifact = br_dir / "testprog.md"
        _write_artifact(
            artifact,
            {
                "type": "business-rules",
                "program": "TESTPROG",
                "program_type": "batch",
                "calls": ["DATEUTIL"],
                "called_by": [],
                "uses_copybooks": ["COCOM01Y"],
                "reads": ["ACCTFILE"],
                "transactions": [],
            },
            "## Program Purpose\n\nProcesses accounts.\n\n"
            "## Input / Output\n\n| Direction | Resource |\n| --- | --- |\n| IN | ACCTFILE |\n\n"
            "## Business Rules\n\n- Rule 1\n\n"
            "## Calculations\n\nNo calculations.\n\n"
            "## Error Handling\n\n- Handles invalid accounts.\n\n"
            "## Control Flow\n\n1. Read\n2. Process\n3. Write\n",
        )
        result = validate_business_rules(artifact, self._make_facts())
        assert result.passed

    def test_repairs_corrupted_frontmatter(self, tmp_path: Path) -> None:
        br_dir = tmp_path / "business-rules"
        br_dir.mkdir()
        artifact = br_dir / "testprog.md"
        _write_artifact(
            artifact,
            {
                "type": "business-rules",
                "program": "TESTPROG",
                "program_type": "online",  # wrong
                "calls": [],  # wrong
                "called_by": [],
                "uses_copybooks": [],  # wrong
                "reads": [],  # wrong
                "transactions": [],
            },
            "## Program Purpose\n\nPurpose.\n\n"
            "## Business Rules\n\n- Rule 1\n\n"
            "## Error Handling\n\n- Error.\n\n"
            "## Control Flow\n\n1. Step.\n",
        )
        result = validate_business_rules(artifact, self._make_facts())
        assert len(result.frontmatter_repairs) > 0

        content = artifact.read_text(encoding="utf-8")
        assert "program_type: batch" in content
        assert "DATEUTIL" in content

    def test_incomplete_sections(self, tmp_path: Path) -> None:
        br_dir = tmp_path / "business-rules"
        br_dir.mkdir()
        artifact = br_dir / "testprog.md"
        _write_artifact(
            artifact,
            {
                "type": "business-rules",
                "program": "TESTPROG",
                "program_type": "batch",
                "calls": ["DATEUTIL"],
                "called_by": [],
                "uses_copybooks": ["COCOM01Y"],
                "reads": ["ACCTFILE"],
                "transactions": [],
            },
            "## Program Purpose\n\nPurpose here.\n\n"
            "## Business Rules\n\n"  # empty
            "## Error Handling\n\n"  # empty
            "## Control Flow\n\n1. Step.\n",
        )
        result = validate_business_rules(artifact, self._make_facts())
        assert "## Business Rules" in result.incomplete_sections
        assert "## Error Handling" in result.incomplete_sections

    def test_missing_file(self, tmp_path: Path) -> None:
        result = validate_business_rules(
            tmp_path / "missing.md", self._make_facts()
        )
        assert not result.passed
        assert "FILE_MISSING" in result.incomplete_sections


class TestCleanupStrayFiles:
    def test_deletes_md_at_root(self, tmp_path: Path) -> None:
        (tmp_path / "stray.md").write_text("content")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "legit.md").write_text("content")

        deleted = cleanup_stray_files(tmp_path)
        assert "stray.md" in deleted
        assert not (tmp_path / "stray.md").exists()
        assert (tmp_path / "subdir" / "legit.md").exists()

    def test_ignores_non_md(self, tmp_path: Path) -> None:
        (tmp_path / "config.yaml").write_text("content")
        deleted = cleanup_stray_files(tmp_path)
        assert len(deleted) == 0
        assert (tmp_path / "config.yaml").exists()


# ---------------------------------------------------------------------------
# Phase 4: Test-specs validation
# ---------------------------------------------------------------------------

_BEHAVIORAL_TESTS_BODY = """\
# Behavioral Test Specifications

## Test Design Principles

| Principle | Description |
| --------- | ----------- |
| Black-box | Tests are black-box |

---

## Customer Enquiry

### Overview

| Property | Value |
| -------- | ----- |
| Capability | Customer Enquiry |
| Source Rules | BR-INQCUST-1 |
| Confidence | high |

### Scenarios

| # | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| - | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1 | Retrieve customer | happy-path | Customer exists | Valid number | Customer returned | no | BR-INQCUST-1 |
| 2 | Customer not found | error | No such customer | Bad number | Failure | no | BR-INQCUST-2 |
| 3 | Minimum customer number | boundary | Customer 1 exists | Number 1 | Customer returned | yes | BR-INQCUST-3 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer number | ID | 1-9999999999 | Existing; Not found | 1, 9999999999 |

---

## Account Creation

### Overview

| Property | Value |
| -------- | ----- |
| Capability | Account Creation |
| Source Rules | BR-CREACC-1 |
| Confidence | medium |

### Scenarios

| # | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| - | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1 | Create ISA | happy-path | Customer exists | ISA type | Account created | no | BR-CREACC-1 |
| 2 | Invalid type | error | Customer exists | Bad type | Rejected | no | BR-CREACC-2 |
| 3 | Customer missing | error | No customer | Valid type | Rejected | no | BR-CREACC-3 |
| 4 | Max account limit | boundary | 9 accounts | Valid type | Account created | yes | BR-CREACC-4 |
| 5 | Create LOAN | happy-path | Customer exists | LOAN type | Account created | no | BR-CREACC-5 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Account type | Type | 8 chars | Valid 5 types; Invalid | ISA, blank |

---

## Cross-Capability Scenarios

| # | Scenario | Capabilities Involved | Preconditions | Input | Expected Output | Source Rules |
| - | -------- | --------------------- | ------------- | ----- | --------------- | ------------ |
| CC-1 | Create then enquire | Creation, Enquiry | Running | Valid data | Data matches | BR-CREACC-1 |
| CC-2 | Delete then confirm | Deletion, Enquiry | Customer exists | Valid ID | Not found | BR-DELCUS-1 |
"""

_EQUIV_MATRIX_BODY = """\
# Equivalence Matrix

## Traceability

| Test ID | Capability | Scenario | Business Rules | Source Programs | Source Paragraphs |
| ------- | ---------- | -------- | -------------- | --------------- | ----------------- |
| T-001 | Customer Enquiry | Retrieve customer | BR-INQCUST-1 | INQCUST | P010 line 178 |

---

## Coverage Summary

| Capability | Total Tests | Happy Path | Error | Boundary | Confidence |
| ---------- | ----------- | ---------- | ----- | -------- | ---------- |
| Customer Enquiry | 3 | 2 | 1 | 1 | high |
| Account Creation | 5 | 3 | 3 | 0 | medium |
| Cross-capability End-to-End | 2 | 2 | 0 | 0 | high |
| **Total** | **10** | **7** | **4** | **1** | **high** |

---

## Untested Rules

| Rule ID | Program | Rule Description | Reason Untested | Priority |
| ------- | ------- | ---------------- | --------------- | -------- |
| BR-TEST-1 | TESTPROG | Some rule | Cannot test | Low |
"""


class TestComputeCoverageSummary:
    def _setup_files(self, tmp_path: Path) -> Path:
        ts_dir = tmp_path / "test-specs"
        ts_dir.mkdir(parents=True)
        _write_artifact(
            ts_dir / "behavioral-tests.md",
            {"type": "test-specifications", "subtype": "behavioral-tests",
             "status": "draft", "confidence": "high", "last_pass": 1},
            _BEHAVIORAL_TESTS_BODY,
        )
        _write_artifact(
            ts_dir / "equivalence-matrix.md",
            {"type": "test-specifications", "subtype": "equivalence-matrix",
             "status": "draft", "confidence": "high", "last_pass": 1},
            _EQUIV_MATRIX_BODY,
        )
        return tmp_path

    def test_corrects_wrong_counts(self, tmp_path: Path) -> None:
        output_dir = self._setup_files(tmp_path)
        corrections = compute_coverage_summary(output_dir)
        assert len(corrections) > 0

        content = (output_dir / "test-specs" / "equivalence-matrix.md").read_text()
        assert "| Customer Enquiry | 3 | 1 | 1 | 1 | high |" in content
        assert "| Account Creation | 5 | 2 | 2 | 1 | medium |" in content

    def test_correct_totals(self, tmp_path: Path) -> None:
        output_dir = self._setup_files(tmp_path)
        compute_coverage_summary(output_dir)

        content = (output_dir / "test-specs" / "equivalence-matrix.md").read_text()
        assert "**10**" in content
        assert "**5**" in content  # 1+2+2 happy-path
        assert "**3**" in content  # 1+2 error

    def test_cross_capability_counted_as_happy_path(self, tmp_path: Path) -> None:
        output_dir = self._setup_files(tmp_path)
        compute_coverage_summary(output_dir)

        content = (output_dir / "test-specs" / "equivalence-matrix.md").read_text()
        assert "| Cross-capability End-to-End | 2 | 2 | 0 | 0 | high |" in content

    def test_preserves_confidence(self, tmp_path: Path) -> None:
        output_dir = self._setup_files(tmp_path)
        compute_coverage_summary(output_dir)

        content = (output_dir / "test-specs" / "equivalence-matrix.md").read_text()
        for line in content.splitlines():
            if "Account Creation" in line and line.startswith("|"):
                assert "medium" in line
                break

    def test_missing_files_returns_empty(self, tmp_path: Path) -> None:
        corrections = compute_coverage_summary(tmp_path)
        assert corrections == []


class TestCheckCapabilityCompleteness:
    def _setup_files(self, tmp_path: Path, cap_names: list[str],
                     bt_sections: list[str]) -> Path:
        req_dir = tmp_path / "requirements"
        req_dir.mkdir(parents=True)
        ts_dir = tmp_path / "test-specs"
        ts_dir.mkdir(parents=True)

        caps_body = "# Functional Capabilities\n\n## Capabilities\n\n"
        for name in cap_names:
            caps_body += f"### {name}\n\nDescription of {name}.\n\n"
        _write_artifact(
            req_dir / "capabilities.md",
            {"type": "requirements", "subtype": "capabilities"},
            caps_body,
        )

        bt_body = "# Behavioral Test Specifications\n\n"
        for name in bt_sections:
            bt_body += f"## {name}\n\nTests for {name}.\n\n"
        _write_artifact(
            ts_dir / "behavioral-tests.md",
            {"type": "test-specifications", "subtype": "behavioral-tests"},
            bt_body,
        )
        return tmp_path

    def test_all_capabilities_covered(self, tmp_path: Path) -> None:
        caps = ["Customer Enquiry", "Account Creation"]
        output_dir = self._setup_files(tmp_path, caps, caps)
        missing = check_capability_completeness(output_dir)
        assert missing == []

    def test_missing_capability_flagged(self, tmp_path: Path) -> None:
        caps = ["Customer Enquiry", "Account Creation", "Fund Transfer"]
        bt = ["Customer Enquiry", "Account Creation"]
        output_dir = self._setup_files(tmp_path, caps, bt)
        missing = check_capability_completeness(output_dir)
        assert "Fund Transfer" in missing
        assert len(missing) == 1

    def test_missing_files_returns_empty(self, tmp_path: Path) -> None:
        missing = check_capability_completeness(tmp_path)
        assert missing == []

    def test_gaps_and_assumptions_excluded(self, tmp_path: Path) -> None:
        caps = ["Customer Enquiry", "Gaps and Assumptions"]
        bt = ["Customer Enquiry"]
        output_dir = self._setup_files(tmp_path, caps, bt)
        missing = check_capability_completeness(output_dir)
        assert missing == []


class TestValidateTestSpecsOutputs:
    def test_integration(self, tmp_path: Path) -> None:
        ts_dir = tmp_path / "test-specs"
        ts_dir.mkdir(parents=True)
        req_dir = tmp_path / "requirements"
        req_dir.mkdir(parents=True)

        _write_artifact(
            ts_dir / "behavioral-tests.md",
            {"type": "test-specifications", "subtype": "behavioral-tests",
             "status": "draft", "confidence": "high", "last_pass": 1},
            _BEHAVIORAL_TESTS_BODY,
        )
        _write_artifact(
            ts_dir / "equivalence-matrix.md",
            {"type": "test-specifications", "subtype": "equivalence-matrix",
             "status": "draft", "confidence": "high", "last_pass": 1},
            _EQUIV_MATRIX_BODY,
        )
        _write_artifact(
            ts_dir / "data-contracts.md",
            {"type": "test-specifications", "subtype": "data-contracts",
             "status": "draft", "confidence": "high", "last_pass": 1},
            "# Data Contract Tests\n\n"
            "## File Contracts\n\n| File | Purpose |\n| --- | --- |\n| F1 | Test |\n\n"
            "## Database Contracts\n\n| Table | Purpose |\n| --- | --- |\n| T1 | Test |\n\n"
            "## Message Contracts\n\n| Queue | Purpose |\n| --- | --- |\n| Q1 | Test |\n\n"
            "## Data Invariants\n\n| # | Invariant |\n| --- | --- |\n| 1 | Some rule |\n",
        )

        caps_body = (
            "# Capabilities\n\n## Capabilities\n\n"
            "### Customer Enquiry\n\nDesc.\n\n"
            "### Account Creation\n\nDesc.\n\n"
            "### Fund Transfer\n\nDesc.\n\n"
        )
        _write_artifact(
            req_dir / "capabilities.md",
            {"type": "requirements", "subtype": "capabilities"},
            caps_body,
        )

        results = validate_test_specs_outputs(tmp_path)

        all_paths = [r.path for r in results]
        assert any("behavioral-tests.md" in p for p in all_paths)
        assert any("equivalence-matrix.md" in p for p in all_paths)
        assert any("data-contracts.md" in p for p in all_paths)

        missing_cap_results = [
            r for r in results
            if any("MISSING_CAPABILITY" in s for s in r.incomplete_sections)
        ]
        assert len(missing_cap_results) == 1
        assert any("Fund Transfer" in s for s in missing_cap_results[0].incomplete_sections)
