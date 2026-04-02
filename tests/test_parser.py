"""Tests for orchestrator.parser -- deterministic COBOL structural parsing."""

from __future__ import annotations

import pytest

from orchestrator.parser import (
    build_chunks,
    classify_paragraph,
    extract_facts,
    extract_performs,
    parse_divisions,
    parse_paragraphs,
    parse_program,
    resolve_thru_ranges,
)
from orchestrator.models import Paragraph


class TestParseDivisions:
    def test_all_four_divisions(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        assert "identification" in divs
        assert "environment" in divs
        assert "data" in divs
        assert "procedure" in divs

    def test_division_order(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        assert divs["identification"][0] < divs["environment"][0]
        assert divs["environment"][0] < divs["data"][0]
        assert divs["data"][0] < divs["procedure"][0]

    def test_procedure_ends_at_file_end(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        assert divs["procedure"][1] == len(batch_program_lines)

    def test_skips_comment_lines(self) -> None:
        lines = """\
      * IDENTIFICATION DIVISION.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TESTPROG.
       PROCEDURE DIVISION.
""".splitlines(keepends=True)
        divs = parse_divisions(lines)
        assert "identification" in divs
        assert divs["identification"][0] == 2

    def test_missing_procedure(self) -> None:
        lines = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MINIMAL.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-VAR PIC X.
""".splitlines(keepends=True)
        divs = parse_divisions(lines)
        assert "procedure" not in divs


class TestParseParagraphs:
    def test_paragraph_count(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        names = [p.name for p in paras]
        assert "0000-MAIN" in names
        assert "1000-INIT" in names
        assert "2000-PROCESS" in names
        assert "2100-READ-RECORD" in names
        assert "3000-CLEANUP" in names

    def test_exit_paragraphs_detected(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        exit_names = [p.name for p in paras if p.classification == "exit"]
        assert "0000-MAIN-EXIT" in exit_names
        assert "1000-INIT-EXIT" in exit_names

    def test_line_ranges_non_overlapping(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        for i in range(len(paras) - 1):
            assert paras[i].end_line < paras[i + 1].start_line or \
                   paras[i].end_line == paras[i + 1].start_line - 1


class TestClassifyParagraph:
    @pytest.mark.parametrize("name,expected_cls", [
        ("0000-MAIN", "dispatch"),
        ("1000-PROCESS-INPUT", "validation"),
        ("2000-READ-RECORD", "io"),
        ("3000-WRITE-OUTPUT", "io"),
        ("4000-VALIDATE-DATA", "validation"),
        ("5000-SEND-SCREEN", "screen"),
        ("9999-EXIT", "exit"),
        ("MAIN-DISPATCH", "dispatch"),
        ("GET-ACCOUNT", "io"),
        ("DELETE-RECORD", "io"),
    ])
    def test_name_based_classification(self, name: str, expected_cls: str) -> None:
        cls, _ = classify_paragraph(name, [])
        assert cls == expected_cls

    def test_body_based_exec_cics(self) -> None:
        body = ["       EXEC CICS READ FILE('X') END-EXEC\n"]
        cls, priority = classify_paragraph("MISC-PARA", body)
        assert cls == "io"
        assert priority == "HIGH"

    def test_body_based_exec_sql(self) -> None:
        body = ["       EXEC SQL SELECT * FROM T END-EXEC\n"]
        cls, _ = classify_paragraph("MISC-PARA", body)
        assert cls == "io"

    def test_body_based_compute(self) -> None:
        body = ["       COMPUTE WS-TOTAL = WS-A + WS-B\n"]
        cls, _ = classify_paragraph("MISC-PARA", body)
        assert cls == "calculation"

    def test_body_based_evaluate(self) -> None:
        body = ["       EVALUATE TRUE\n", "         WHEN X = 1\n"]
        cls, _ = classify_paragraph("MISC-PARA", body)
        assert cls == "decision"


class TestExtractPerforms:
    def test_simple_perform(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        main = next(p for p in paras if p.name == "0000-MAIN")
        assert "1000-INIT" in main.performs
        assert "2000-PROCESS" in main.performs
        assert "3000-CLEANUP" in main.performs

    def test_perform_thru_same_line(self, perform_thru_lines: list[str]) -> None:
        divs = parse_divisions(perform_thru_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(perform_thru_lines, proc[0], proc[1])
        main = next(p for p in paras if p.name == "0000-MAIN")
        assert ("1000-START", "1000-START-EXIT") in main.perform_thru

    def test_perform_thru_multi_line(self, perform_thru_lines: list[str]) -> None:
        divs = parse_divisions(perform_thru_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(perform_thru_lines, proc[0], proc[1])
        main = next(p for p in paras if p.name == "0000-MAIN")
        assert ("2000-PROCESS", "2000-PROCESS-EXIT") in main.perform_thru

    def test_filters_keywords(self) -> None:
        body = [
            "       PERFORM UNTIL WS-EOF\n",
            "           PERFORM 1000-READ\n",
            "       END-PERFORM\n",
        ]
        performs, _ = extract_performs(body)
        assert "1000-READ" in performs
        assert "UNTIL" not in performs

    def test_deduplicates(self) -> None:
        body = [
            "       PERFORM 1000-READ\n",
            "       PERFORM 1000-READ\n",
        ]
        performs, _ = extract_performs(body)
        assert performs.count("1000-READ") == 1


class TestResolveThruRanges:
    def test_range_includes_intermediate(self, perform_thru_lines: list[str]) -> None:
        divs = parse_divisions(perform_thru_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(perform_thru_lines, proc[0], proc[1])
        ranges = resolve_thru_ranges(paras)
        range_map = {start: members for start, members in ranges}
        assert "1000-START" in range_map
        assert "1000-START-EXIT" in range_map["1000-START"]


class TestBuildChunks:
    def test_creates_chunks(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        chunks = build_chunks(paras, chunk_threshold=800)
        assert len(chunks) > 0

    def test_all_paragraphs_assigned(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        chunks = build_chunks(paras, chunk_threshold=800)
        assigned = set()
        for c in chunks:
            assigned.update(c.paragraphs)
        para_names = {p.name for p in paras}
        assert assigned == para_names

    def test_exit_follows_entry(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        proc = divs["procedure"]
        paras = parse_paragraphs(batch_program_lines, proc[0], proc[1])
        chunks = build_chunks(paras, chunk_threshold=800)
        for c in chunks:
            for name in c.paragraphs:
                if name.endswith("-EXIT"):
                    entry = name[:-5]
                    if entry in {p.name for p in paras}:
                        assert entry in c.paragraphs, \
                            f"{name} should be in the same chunk as {entry}"


class TestExtractFacts:
    def test_batch_program_type(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        facts = extract_facts("TESTPROG", "/path/test.cbl", batch_program_lines, divs)
        assert facts.program_type == "batch"
        assert facts.program == "TESTPROG"

    def test_online_program_type(self, online_program_lines: list[str]) -> None:
        divs = parse_divisions(online_program_lines)
        facts = extract_facts("ONLNPROG", "/path/onln.cbl", online_program_lines, divs)
        assert facts.program_type == "online"

    def test_subprogram_detection(self, db2_program_lines: list[str]) -> None:
        divs = parse_divisions(db2_program_lines)
        facts = extract_facts("DB2PROG", "/path/db2.cbl", db2_program_lines, divs)
        assert facts.program_type == "subprogram"

    def test_copybook_extraction(self, online_program_lines: list[str]) -> None:
        divs = parse_divisions(online_program_lines)
        facts = extract_facts("ONLNPROG", "/path/onln.cbl", online_program_lines, divs)
        assert "COCOM01Y" in facts.copybooks
        assert "DFHAID" not in facts.copybooks  # system copybook filtered

    def test_file_reads_batch(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        facts = extract_facts("TESTPROG", "/path/test.cbl", batch_program_lines, divs)
        assert "ACCTFILE" in facts.file_reads

    def test_file_reads_cics(self, online_program_lines: list[str]) -> None:
        divs = parse_divisions(online_program_lines)
        facts = extract_facts("ONLNPROG", "/path/onln.cbl", online_program_lines, divs)
        assert "ACCTFIL" in facts.file_reads

    def test_transid_from_literal(self, online_program_lines: list[str]) -> None:
        divs = parse_divisions(online_program_lines)
        facts = extract_facts("ONLNPROG", "/path/onln.cbl", online_program_lines, divs)
        assert facts.transid == "ACCT"

    def test_xctl_targets(self, online_program_lines: list[str]) -> None:
        divs = parse_divisions(online_program_lines)
        facts = extract_facts("ONLNPROG", "/path/onln.cbl", online_program_lines, divs)
        assert "MENUPRG1" in facts.xctl_targets

    def test_call_targets(self, db2_program_lines: list[str]) -> None:
        divs = parse_divisions(db2_program_lines)
        facts = extract_facts("DB2PROG", "/path/db2.cbl", db2_program_lines, divs)
        assert "DATEUTIL" in facts.call_targets

    def test_db_tables(self, db2_program_lines: list[str]) -> None:
        divs = parse_divisions(db2_program_lines)
        facts = extract_facts("DB2PROG", "/path/db2.cbl", db2_program_lines, divs)
        assert "ACCOUNTS" in facts.db_tables
        assert "TRANSACTIONS" in facts.db_tables

    def test_sql_include_copybook(self, db2_program_lines: list[str]) -> None:
        divs = parse_divisions(db2_program_lines)
        facts = extract_facts("DB2PROG", "/path/db2.cbl", db2_program_lines, divs)
        assert "DCLACCTS" in facts.copybooks
        assert "SQLCA" not in facts.copybooks  # system copybook

    def test_loc(self, batch_program_lines: list[str]) -> None:
        divs = parse_divisions(batch_program_lines)
        facts = extract_facts("TESTPROG", "/path/test.cbl", batch_program_lines, divs)
        assert facts.loc == len(batch_program_lines)


class TestParseProgram:
    def test_full_pipeline_batch(self, batch_program_lines: list[str]) -> None:
        manifest = parse_program("/path/test.cbl", batch_program_lines, chunk_threshold=800)
        assert manifest.program == "TESTPROG"
        assert manifest.staged is True
        assert manifest.facts is not None
        assert manifest.facts.program_type == "batch"
        assert len(manifest.paragraphs) > 0
        assert len(manifest.chunks) > 0

    def test_no_procedure_division(self) -> None:
        lines = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. NOPROC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-VAR PIC X.
""".splitlines(keepends=True)
        manifest = parse_program("/path/noproc.cbl", lines)
        assert manifest.staged is False
        assert len(manifest.paragraphs) == 0
        assert len(manifest.chunks) == 0
        assert manifest.facts is not None
