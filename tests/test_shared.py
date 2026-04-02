"""Tests for orchestrator shared utilities (split_frontmatter, etc.)."""

from __future__ import annotations

from pathlib import Path

from orchestrator import (
    discover_program_files,
    read_template,
    split_frontmatter,
)


class TestSplitFrontmatter:
    def test_valid_frontmatter(self) -> None:
        content = "---\ntype: inventory\nsubtype: programs\n---\n\n# Programs\n"
        fm, body = split_frontmatter(content)
        assert fm["type"] == "inventory"
        assert fm["subtype"] == "programs"
        assert body.startswith("# Programs")

    def test_no_frontmatter(self) -> None:
        content = "# Just Markdown\n\nNo frontmatter here.\n"
        fm, body = split_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_unclosed_frontmatter(self) -> None:
        content = "---\ntype: broken\nno closing delimiter\n"
        fm, body = split_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_empty_frontmatter(self) -> None:
        content = "---\n---\n\nBody here.\n"
        fm, body = split_frontmatter(content)
        assert fm == {}
        assert body.startswith("Body here.")


class TestReadTemplate:
    def test_reads_business_rules_template(self) -> None:
        content = read_template("business-rules.md")
        assert len(content) > 0
        assert "---" in content

    def test_reads_all_templates(self) -> None:
        templates = [
            "application.md",
            "business-rules.md",
            "capabilities.md",
            "copybook-inventory.md",
            "data-dictionary.md",
            "file-layouts.md",
            "interfaces.md",
            "modernization-notes.md",
            "program-call-graph.md",
            "program-inventory.md",
        ]
        for name in templates:
            content = read_template(name)
            assert len(content) > 0, f"Template {name} is empty"


class TestDiscoverProgramFiles:
    def test_finds_cbl_files(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        (src_dir / "PROG1.cbl").write_text("       IDENTIFICATION DIVISION.\n")
        (src_dir / "PROG2.cbl").write_text("       IDENTIFICATION DIVISION.\n")
        (src_dir / "COPY1.cpy").write_text("       01 WS-VAR PIC X.\n")

        config = {
            "source": {
                "programs": [str(src_dir)],
                "recursive": False,
                "extensions": {"programs": [".cbl"]},
            },
        }
        files = discover_program_files(config)
        names = [f.stem.upper() for f in files]
        assert "PROG1" in names
        assert "PROG2" in names
        assert "COPY1" not in names

    def test_recursive_search(self, tmp_path: Path) -> None:
        sub = tmp_path / "source" / "subdir"
        sub.mkdir(parents=True)
        (sub / "DEEP.cbl").write_text("       IDENTIFICATION DIVISION.\n")

        config = {
            "source": {
                "programs": [str(tmp_path / "source")],
                "recursive": True,
                "extensions": {"programs": [".cbl"]},
            },
        }
        files = discover_program_files(config)
        assert any(f.stem.upper() == "DEEP" for f in files)

    def test_deduplicates(self, tmp_path: Path) -> None:
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "PROG.cbl").write_text("content")
        (dir2 / "PROG.CBL").write_text("content")

        config = {
            "source": {
                "programs": [str(dir1), str(dir2)],
                "recursive": False,
                "extensions": {"programs": [".cbl", ".CBL"]},
            },
        }
        files = discover_program_files(config)
        prog_names = [f.stem.upper() for f in files]
        assert prog_names.count("PROG") == 1

    def test_empty_dirs(self, tmp_path: Path) -> None:
        config = {
            "source": {
                "programs": [str(tmp_path / "nonexistent")],
                "recursive": True,
                "extensions": {"programs": [".cbl"]},
            },
        }
        files = discover_program_files(config)
        assert files == []

    def test_sorted_output(self, tmp_path: Path) -> None:
        src = tmp_path / "source"
        src.mkdir()
        for name in ["ZZZPROG", "AAAPROG", "MMMPPROG"]:
            (src / f"{name}.cbl").write_text("content")

        config = {
            "source": {
                "programs": [str(src)],
                "recursive": False,
                "extensions": {"programs": [".cbl"]},
            },
        }
        files = discover_program_files(config)
        names = [f.stem.upper() for f in files]
        assert names == sorted(names)
