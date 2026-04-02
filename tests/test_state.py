"""Tests for orchestrator.state -- state persistence and convergence."""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.models import Discovery, IterationResult
from orchestrator.state import (
    OrchestratorState,
    diff_snapshots,
    snapshot_output_dir,
)


class TestOrchestratorState:
    def test_fresh_state(self, tmp_path: Path) -> None:
        state = OrchestratorState(tmp_path / "state.json")
        assert state.current_iteration == 1
        assert state.total_discoveries == 0
        assert state.total_artifacts_written == 0
        assert not state.is_converged()

    def test_record_iteration(self, tmp_path: Path) -> None:
        state = OrchestratorState(tmp_path / "state.json")
        state.start_run()

        result = IterationResult(
            iteration=1,
            discoveries=[
                Discovery("new_artifact", "inventory", "inventory/programs.md",
                          summary="Found 5 programs"),
            ],
            artifacts_written=["inventory/programs.md"],
        )
        state.record_iteration(result)

        assert state.current_iteration == 2
        assert state.total_discoveries == 1
        assert state.total_artifacts_written == 1
        assert state.consecutive_empty == 0

    def test_convergence_after_empty_iterations(self, tmp_path: Path) -> None:
        state = OrchestratorState(tmp_path / "state.json")
        state.start_run()

        state.record_iteration(IterationResult(iteration=1))
        assert not state.is_converged(n_stable=2)

        state.record_iteration(IterationResult(iteration=2))
        assert state.is_converged(n_stable=2)

    def test_convergence_resets_on_discovery(self, tmp_path: Path) -> None:
        state = OrchestratorState(tmp_path / "state.json")
        state.start_run()

        state.record_iteration(IterationResult(iteration=1))
        assert state.consecutive_empty == 1

        result_with_disc = IterationResult(
            iteration=2,
            discoveries=[Discovery("new_artifact", "data", "data/dict.md")],
        )
        state.record_iteration(result_with_disc)
        assert state.consecutive_empty == 0

    def test_save_and_load(self, tmp_path: Path) -> None:
        state_file = tmp_path / "state.json"
        state = OrchestratorState(state_file)
        state.start_run()

        result = IterationResult(
            iteration=1,
            discoveries=[
                Discovery("new_artifact", "inventory", "inventory/programs.md"),
            ],
            artifacts_written=["inventory/programs.md"],
        )
        state.record_iteration(result)
        state.finish_run()

        loaded = OrchestratorState.load(state_file)
        assert loaded.total_discoveries == 1
        assert loaded.total_artifacts_written == 1
        assert len(loaded.iterations) == 1
        assert loaded.started_at is not None

    def test_load_missing_file(self, tmp_path: Path) -> None:
        state = OrchestratorState.load(tmp_path / "nonexistent.json")
        assert state.current_iteration == 1
        assert state.total_discoveries == 0

    def test_finish_sets_completed_at(self, tmp_path: Path) -> None:
        state = OrchestratorState(tmp_path / "state.json")
        state.start_run()
        state.finish_run()
        assert state.completed_at is not None

    def test_start_run_idempotent_on_loaded_state(self, tmp_path: Path) -> None:
        state_file = tmp_path / "state.json"
        state = OrchestratorState(state_file)
        state.start_run()
        state.record_iteration(IterationResult(iteration=1))
        state.finish_run()

        loaded = OrchestratorState.load(state_file)
        original_started = loaded.started_at
        loaded.start_run()
        assert loaded.started_at == original_started


class TestSnapshotDiff:
    def test_created_files(self, tmp_path: Path) -> None:
        before: dict[str, tuple[float, int]] = {}
        (tmp_path / "new.md").write_text("content")
        after = snapshot_output_dir(tmp_path)
        created, modified, deleted = diff_snapshots(before, after)
        assert "new.md" in created
        assert not modified
        assert not deleted

    def test_modified_files(self, tmp_path: Path) -> None:
        (tmp_path / "file.md").write_text("v1")
        before = snapshot_output_dir(tmp_path)
        (tmp_path / "file.md").write_text("v2 - longer content")
        after = snapshot_output_dir(tmp_path)
        created, modified, deleted = diff_snapshots(before, after)
        assert "file.md" in modified

    def test_deleted_files(self, tmp_path: Path) -> None:
        (tmp_path / "file.md").write_text("content")
        before = snapshot_output_dir(tmp_path)
        (tmp_path / "file.md").unlink()
        after = snapshot_output_dir(tmp_path)
        created, modified, deleted = diff_snapshots(before, after)
        assert "file.md" in deleted

    def test_empty_dir(self, tmp_path: Path) -> None:
        snap = snapshot_output_dir(tmp_path)
        assert snap == {}

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        snap = snapshot_output_dir(tmp_path / "no-such-dir")
        assert snap == {}
