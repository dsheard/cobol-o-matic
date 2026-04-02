"""Tests for orchestrator.models -- dataclass serialization round-trips."""

from __future__ import annotations

from orchestrator.models import (
    Chunk,
    Discovery,
    IterationResult,
    Paragraph,
    ProgramFacts,
    ProgramManifest,
)


class TestDiscovery:
    def test_round_trip(self) -> None:
        d = Discovery(
            discovery_type="new_artifact",
            artifact_type="business-rules",
            artifact_path="business-rules/testprog.md",
            program="TESTPROG",
            summary="Found 5 business rules",
            confidence="high",
        )
        d2 = Discovery.from_dict(d.to_dict())
        assert d2.discovery_type == d.discovery_type
        assert d2.artifact_path == d.artifact_path
        assert d2.program == d.program
        assert d2.confidence == d.confidence

    def test_from_dict_fallback_keys(self) -> None:
        data = {
            "type": "updated_artifact",
            "artifact_type": "flow",
            "path": "flows/call-graph.md",
        }
        d = Discovery.from_dict(data)
        assert d.discovery_type == "updated_artifact"
        assert d.artifact_path == "flows/call-graph.md"

    def test_dedup_key(self) -> None:
        d = Discovery(
            discovery_type="new_artifact",
            artifact_type="inventory",
            artifact_path="inventory/programs.md",
        )
        assert d.key == "new_artifact:inventory/inventory/programs.md"


class TestIterationResult:
    def test_round_trip(self) -> None:
        result = IterationResult(
            iteration=1,
            discoveries=[
                Discovery("new_artifact", "inventory", "inventory/programs.md"),
            ],
            artifacts_written=["inventory/programs.md"],
        )
        data = result.to_dict()
        assert data["iteration"] == 1
        assert len(data["discoveries"]) == 1
        assert data["artifacts_written"] == ["inventory/programs.md"]


class TestParagraph:
    def test_to_dict(self) -> None:
        p = Paragraph(
            name="1000-MAIN",
            start_line=50,
            end_line=75,
            classification="dispatch",
            priority="HIGH",
            performs=["2000-PROCESS"],
            perform_thru=[("2000-PROCESS", "2000-PROCESS-EXIT")],
        )
        d = p.to_dict()
        assert d["name"] == "1000-MAIN"
        assert d["perform_thru"] == [["2000-PROCESS", "2000-PROCESS-EXIT"]]


class TestProgramFacts:
    def test_round_trip(self) -> None:
        facts = ProgramFacts(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=500,
            program_type="online",
            copybooks=["COCOM01Y"],
            file_reads=["ACCTFIL"],
            call_targets=["DATEUTIL"],
            xctl_targets=["MENUPROG"],
            db_tables=["ACCOUNTS"],
            transid="ACCT",
        )
        d = facts.to_dict()
        facts2 = ProgramFacts.from_dict(d)
        assert facts2.program == "TESTPROG"
        assert facts2.program_type == "online"
        assert facts2.transid == "ACCT"
        assert facts2.copybooks == ["COCOM01Y"]
        assert facts2.db_tables == ["ACCOUNTS"]

    def test_from_dict_defaults(self) -> None:
        facts = ProgramFacts.from_dict({"program": "MINIMAL"})
        assert facts.loc == 0
        assert facts.program_type == "batch"
        assert facts.copybooks == []
        assert facts.transid is None


class TestProgramManifest:
    def test_round_trip(self) -> None:
        manifest = ProgramManifest(
            program="TESTPROG",
            source_path="/path/test.cbl",
            loc=300,
            data_division_range=(10, 50),
            procedure_division_range=(51, 300),
            paragraphs=[
                Paragraph("0000-MAIN", 52, 60, "dispatch", "HIGH",
                          performs=["1000-INIT"]),
                Paragraph("1000-INIT", 62, 70, "io", "HIGH"),
            ],
            chunks=[
                Chunk("dispatch", ["0000-MAIN"], 52, 60, "dispatch"),
                Chunk("io", ["1000-INIT"], 62, 70, "io"),
            ],
            staged=True,
            facts=ProgramFacts(
                program="TESTPROG",
                source_path="/path/test.cbl",
                loc=300,
                program_type="batch",
            ),
        )
        d = manifest.to_dict()
        m2 = ProgramManifest.from_dict(d)
        assert m2.program == "TESTPROG"
        assert m2.loc == 300
        assert m2.data_division_range == (10, 50)
        assert len(m2.paragraphs) == 2
        assert len(m2.chunks) == 2
        assert m2.staged is True
        assert m2.facts is not None
        assert m2.facts.program_type == "batch"

    def test_round_trip_no_facts(self) -> None:
        manifest = ProgramManifest(
            program="NOFACTS",
            source_path="/path/nofacts.cbl",
            loc=100,
            data_division_range=(10, 50),
            procedure_division_range=(51, 100),
        )
        d = manifest.to_dict()
        assert "facts" not in d
        m2 = ProgramManifest.from_dict(d)
        assert m2.facts is None
