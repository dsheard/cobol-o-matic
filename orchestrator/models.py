"""Data models for the COBOL reverse-engineering orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Discovery:
    """A single discovery made by a worker during an iteration.

    Discoveries are the unit of convergence: the loop stops when no new
    discoveries are produced for N consecutive iterations.
    """

    discovery_type: str  # "new_artifact" | "updated_artifact" | "new_reference"
    artifact_type: str   # ArtifactType value
    artifact_path: str   # relative path under output/
    program: str = ""
    summary: str = ""
    confidence: str = "medium"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Discovery:
        mapped = {}
        for k, v in data.items():
            if k in cls.__dataclass_fields__:
                mapped[k] = v
        if "discovery_type" not in mapped:
            mapped["discovery_type"] = data.get("type", "new_artifact")
        if "artifact_path" not in mapped:
            mapped["artifact_path"] = data.get("path", "")
        return cls(**mapped)

    @property
    def key(self) -> str:
        """Deduplication key."""
        return f"{self.discovery_type}:{self.artifact_type}/{self.artifact_path}"


@dataclass
class IterationResult:
    """Result of a single orchestrator iteration."""

    iteration: int
    discoveries: list[Discovery] = field(default_factory=list)
    artifacts_written: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "discoveries": [d.to_dict() for d in self.discoveries],
            "artifacts_written": self.artifacts_written,
        }


# ---------------------------------------------------------------------------
# Staging / chunking models
# ---------------------------------------------------------------------------


@dataclass
class Paragraph:
    """A single COBOL paragraph extracted from the PROCEDURE DIVISION."""

    name: str
    start_line: int
    end_line: int
    classification: str  # dispatch, validation, decision, io, screen, exit, other
    priority: str  # HIGH, LOW, SKIP
    performs: list[str] = field(default_factory=list)
    perform_thru: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "classification": self.classification,
            "priority": self.priority,
            "performs": self.performs,
            "perform_thru": [list(t) for t in self.perform_thru],
        }


@dataclass
class ProgramFacts:
    """Deterministically extracted metadata for a COBOL program.

    All fields are populated by regex-based extraction in parser.extract_facts(),
    not by LLM inference.  Used to pre-populate output file frontmatter and to
    validate agent outputs.
    """

    program: str
    source_path: str
    loc: int
    program_type: str  # online | batch | subprogram
    copybooks: list[str] = field(default_factory=list)
    literals: dict[str, str] = field(default_factory=dict)
    file_reads: list[str] = field(default_factory=list)
    call_targets: list[str] = field(default_factory=list)
    xctl_targets: list[str] = field(default_factory=list)
    db_tables: list[str] = field(default_factory=list)
    transid: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ProgramFacts:
        return cls(
            program=data["program"],
            source_path=data.get("source_path", ""),
            loc=data.get("loc", 0),
            program_type=data.get("program_type", "batch"),
            copybooks=data.get("copybooks", []),
            literals=data.get("literals", {}),
            file_reads=data.get("file_reads", []),
            call_targets=data.get("call_targets", []),
            xctl_targets=data.get("xctl_targets", []),
            db_tables=data.get("db_tables", []),
            transid=data.get("transid"),
        )


@dataclass
class Chunk:
    """A group of related paragraphs staged as a single file for agent analysis."""

    chunk_id: str
    paragraphs: list[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    classification: str = "other"

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "file": f"chunk-{self.chunk_id}.cbl",
            "paragraphs": self.paragraphs,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "classification": self.classification,
        }


@dataclass
class ProgramManifest:
    """Full structural manifest for a staged COBOL program."""

    program: str
    source_path: str
    loc: int
    data_division_range: tuple[int, int]
    procedure_division_range: tuple[int, int]
    paragraphs: list[Paragraph] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    staged: bool = False
    facts: ProgramFacts | None = None

    def to_dict(self) -> dict:
        d = {
            "program": self.program,
            "source_path": self.source_path,
            "loc": self.loc,
            "data_division": {
                "start_line": self.data_division_range[0],
                "end_line": self.data_division_range[1],
            },
            "procedure_division": {
                "start_line": self.procedure_division_range[0],
                "end_line": self.procedure_division_range[1],
            },
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "chunks": [c.to_dict() for c in self.chunks],
            "staged": self.staged,
        }
        if self.facts:
            d["facts"] = self.facts.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ProgramManifest:
        dd = data.get("data_division", {})
        pd_ = data.get("procedure_division", {})
        paragraphs = [
            Paragraph(
                name=p["name"],
                start_line=p["start_line"],
                end_line=p["end_line"],
                classification=p.get("classification", "other"),
                priority=p.get("priority", "HIGH"),
                performs=p.get("performs", []),
                perform_thru=[tuple(t) for t in p.get("perform_thru", [])],
            )
            for p in data.get("paragraphs", [])
        ]
        chunks = [
            Chunk(
                chunk_id=c["chunk_id"],
                paragraphs=c.get("paragraphs", []),
                start_line=c.get("start_line", 0),
                end_line=c.get("end_line", 0),
                classification=c.get("classification", "other"),
            )
            for c in data.get("chunks", [])
        ]
        facts_data = data.get("facts")
        facts = ProgramFacts.from_dict(facts_data) if facts_data else None
        return cls(
            program=data["program"],
            source_path=data.get("source_path", ""),
            loc=data.get("loc", 0),
            data_division_range=(dd.get("start_line", 0), dd.get("end_line", 0)),
            procedure_division_range=(pd_.get("start_line", 0), pd_.get("end_line", 0)),
            paragraphs=paragraphs,
            chunks=chunks,
            staged=data.get("staged", False),
            facts=facts,
        )
