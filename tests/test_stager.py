"""Tests for orchestrator.stager -- staging pipeline and output pre-population."""

from __future__ import annotations

from pathlib import Path

import yaml

from orchestrator.models import ProgramFacts, ProgramManifest
from orchestrator.stager import (
    MANIFEST_FILENAME,
    get_manifest,
    needs_restaging,
    prepopulate_business_rules,
    stage_program,
)
from orchestrator import split_frontmatter


def _write_cobol(path: Path, program_id: str = "TESTPROG", lines: int = 100) -> Path:
    """Write a minimal COBOL program with enough structure to parse."""
    src = f"""\
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    {program_id}.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-FLAG           PIC X(1) VALUE 'N'.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-PROCESS
           STOP RUN.

       0000-MAIN-EXIT.
           EXIT.

       1000-PROCESS.
           IF WS-FLAG = 'Y'
               DISPLAY 'YES'
           END-IF.

       1000-PROCESS-EXIT.
           EXIT.
"""
    padding = "\n".join(f"      * Line {i}" for i in range(lines - 25))
    content = src + padding + "\n"
    path.write_text(content, encoding="utf-8")
    return path


class TestStageProgram:
    def test_creates_manifest(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        manifest = stage_program(source, staging, chunk_threshold=800)

        assert manifest.program == "TESTPROG"
        manifest_file = staging / "testprog" / MANIFEST_FILENAME
        assert manifest_file.is_file()

    def test_creates_chunk_files(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        manifest = stage_program(source, staging, chunk_threshold=800)

        for chunk in manifest.chunks:
            chunk_file = staging / "testprog" / f"chunk-{chunk.chunk_id}.cbl"
            assert chunk_file.is_file(), f"Missing chunk file: {chunk_file}"

    def test_creates_data_division(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        stage_program(source, staging, chunk_threshold=800)

        dd_file = staging / "testprog" / "data-division.cbl"
        assert dd_file.is_file()

    def test_manifest_roundtrips(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        stage_program(source, staging, chunk_threshold=800)

        loaded = get_manifest(staging, "TESTPROG")
        assert loaded is not None
        assert loaded.program == "TESTPROG"
        assert loaded.staged is True

    def test_cleans_stale_chunks(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        stage_program(source, staging, chunk_threshold=800)
        stale = staging / "testprog" / "chunk-old.cbl"
        stale.write_text("stale content")

        stage_program(source, staging, chunk_threshold=800)
        assert not stale.exists()

    def test_facts_populated(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"

        manifest = stage_program(source, staging, chunk_threshold=800)

        assert manifest.facts is not None
        assert manifest.facts.program == "TESTPROG"
        assert manifest.facts.program_type == "batch"


class TestNeedsRestaging:
    def test_no_manifest_needs_staging(self, tmp_path: Path) -> None:
        source = tmp_path / "test.cbl"
        source.write_text("content")
        assert needs_restaging(source, tmp_path / "manifest.yaml") is True

    def test_current_manifest_skips(self, tmp_path: Path) -> None:
        source = tmp_path / "test.cbl"
        source.write_text("content")
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("manifest data")
        assert needs_restaging(source, manifest) is False

    def test_stale_manifest_needs_staging(self, tmp_path: Path) -> None:
        import time

        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("old manifest")
        time.sleep(0.05)
        source = tmp_path / "test.cbl"
        source.write_text("newer content")
        assert needs_restaging(source, manifest) is True


class TestGetManifest:
    def test_returns_none_for_missing(self, tmp_path: Path) -> None:
        assert get_manifest(tmp_path, "NOPROG") is None

    def test_loads_valid_manifest(self, tmp_path: Path) -> None:
        source = _write_cobol(tmp_path / "test.cbl")
        staging = tmp_path / "staging"
        stage_program(source, staging, chunk_threshold=800)

        manifest = get_manifest(staging, "TESTPROG")
        assert manifest is not None
        assert manifest.program == "TESTPROG"


class TestPrepopulateBusinessRules:
    def test_creates_output_file(self, tmp_path: Path) -> None:
        facts = ProgramFacts(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=200,
            program_type="batch",
            copybooks=["COCOM01Y"],
            file_reads=["ACCTFILE"],
            call_targets=["DATEUTIL"],
            transid=None,
        )
        output = tmp_path / "output"
        path = prepopulate_business_rules(facts, output)

        assert path.is_file()
        assert path.name == "testprog.md"

        content = path.read_text(encoding="utf-8")
        fm, _ = split_frontmatter(content)
        assert fm["program"] == "TESTPROG"
        assert fm["program_type"] == "batch"
        assert fm["calls"] == ["DATEUTIL"]
        assert fm["uses_copybooks"] == ["COCOM01Y"]
        assert fm["reads"] == ["ACCTFILE"]

    def test_skips_existing_content(self, tmp_path: Path) -> None:
        facts = ProgramFacts(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=200,
            program_type="batch",
        )
        output = tmp_path / "output"
        path = prepopulate_business_rules(facts, output)
        original_content = path.read_text()

        big_content = original_content + "\n\n## Extra Content\n\nLots of analysis here.\n" * 10
        path.write_text(big_content)

        prepopulate_business_rules(facts, output)
        assert path.read_text() == big_content  # not overwritten

    def test_includes_called_by(self, tmp_path: Path) -> None:
        facts = ProgramFacts(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=200,
            program_type="batch",
        )
        output = tmp_path / "output"
        path = prepopulate_business_rules(facts, output, called_by=["MAINPROG"])

        fm, _ = split_frontmatter(path.read_text())
        assert fm["called_by"] == ["MAINPROG"]

    def test_transid_in_frontmatter(self, tmp_path: Path) -> None:
        facts = ProgramFacts(
            program="ONLNPROG",
            source_path="/path/onln.cbl",
            loc=300,
            program_type="online",
            transid="ACCT",
        )
        output = tmp_path / "output"
        path = prepopulate_business_rules(facts, output)

        fm, _ = split_frontmatter(path.read_text())
        assert fm["transactions"] == ["ACCT"]
