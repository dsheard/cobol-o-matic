"""State management -- persists orchestrator state between iterations and runs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import Discovery, IterationResult

logger = logging.getLogger(__name__)


class OrchestratorState:
    """Tracks iterations, discoveries, and artifacts written across runs."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.iterations: list[IterationResult] = []
        self.all_artifacts_written: list[str] = []
        self.all_discoveries: list[dict] = []
        self.started_at: str | None = None
        self.completed_at: str | None = None
        self.consecutive_empty: int = 0

    def start_run(self) -> None:
        """Initialize a run if this is a fresh state.

        If state has already been loaded (resume scenario), preserves existing
        timestamps and convergence counters.
        """
        if self.started_at is None and not self.iterations:
            self.started_at = datetime.now(timezone.utc).isoformat()
            self.consecutive_empty = 0
        else:
            logger.debug(
                "start_run called on existing state; "
                "preserving started_at=%s, consecutive_empty=%d",
                self.started_at,
                self.consecutive_empty,
            )

    def record_iteration(self, result: IterationResult) -> None:
        self.iterations.append(result)
        self.all_artifacts_written.extend(result.artifacts_written)
        self.all_discoveries.extend(d.to_dict() for d in result.discoveries)

        if len(result.discoveries) == 0:
            self.consecutive_empty += 1
        else:
            self.consecutive_empty = 0

        self._save()

    def is_converged(self, n_stable: int = 2) -> bool:
        return self.consecutive_empty >= n_stable

    @property
    def is_completed(self) -> bool:
        """True if this phase/program already ran to completion."""
        return self.completed_at is not None

    def finish_run(self) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self._save()

    @property
    def current_iteration(self) -> int:
        return len(self.iterations) + 1

    @property
    def total_discoveries(self) -> int:
        return len(self.all_discoveries)

    @property
    def total_artifacts_written(self) -> int:
        return len(self.all_artifacts_written)

    def _save(self) -> None:
        data = {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_iterations": len(self.iterations),
            "total_discoveries": self.total_discoveries,
            "total_artifacts_written": self.total_artifacts_written,
            "consecutive_empty_iterations": self.consecutive_empty,
            "all_artifacts_written": self.all_artifacts_written,
            "iterations": [it.to_dict() for it in self.iterations],
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
        logger.debug("State saved to %s", self.state_file)

    @classmethod
    def load(cls, state_file: Path) -> OrchestratorState:
        """Load state from a previous run for resumption."""
        state = cls(state_file)
        if not state_file.is_file():
            return state

        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load state file: %s", e)
            return state

        state.started_at = data.get("started_at")
        state.completed_at = data.get("completed_at")
        state.all_artifacts_written = data.get("all_artifacts_written", [])
        state.consecutive_empty = data.get("consecutive_empty_iterations", 0)

        for it_data in data.get("iterations", []):
            discoveries = [
                Discovery.from_dict(d) for d in it_data.get("discoveries", [])
            ]
            result = IterationResult(
                iteration=it_data.get("iteration", 0),
                discoveries=discoveries,
                artifacts_written=it_data.get("artifacts_written", []),
            )
            state.iterations.append(result)
            state.all_discoveries.extend(d.to_dict() for d in discoveries)

        logger.info(
            "Resumed from state: %d iterations, %d artifacts written",
            len(state.iterations),
            state.total_artifacts_written,
        )
        return state


# ---------------------------------------------------------------------------
# File-change tracking
# ---------------------------------------------------------------------------

FileSnapshot = dict[str, tuple[float, int]]


def snapshot_output_dir(output_dir: Path) -> FileSnapshot:
    """Capture mtime and size for every .md file under output_dir."""
    snap: FileSnapshot = {}
    if not output_dir.is_dir():
        return snap
    for md_file in output_dir.rglob("*.md"):
        rel = str(md_file.relative_to(output_dir))
        stat = md_file.stat()
        snap[rel] = (stat.st_mtime, stat.st_size)
    return snap


def diff_snapshots(
    before: FileSnapshot,
    after: FileSnapshot,
) -> tuple[list[str], list[str], list[str]]:
    """Compare two snapshots.  Returns (created, modified, deleted)."""
    created = [p for p in after if p not in before]
    deleted = [p for p in before if p not in after]
    modified = [
        p for p in after
        if p in before and after[p] != before[p]
    ]
    return sorted(created), sorted(modified), sorted(deleted)


def print_file_changes(
    label: str,
    output_dir: Path,
    before: FileSnapshot,
    after: FileSnapshot,
) -> None:
    """Print a summary of file changes between two snapshots."""
    created, modified, deleted = diff_snapshots(before, after)

    if not created and not modified and not deleted:
        print(f"\n  {label}: no file changes")
        return

    divider = "-" * 40
    print(f"\n  {divider}")
    print(f"  {label} file changes")
    print(f"  {divider}")

    for rel_path in created:
        size = (output_dir / rel_path).stat().st_size
        print(f"  CREATED:  {rel_path} ({size:,} bytes)")
    for rel_path in modified:
        size = (output_dir / rel_path).stat().st_size
        print(f"  MODIFIED: {rel_path} ({size:,} bytes)")
    for rel_path in deleted:
        print(f"  DELETED:  {rel_path}")

    print(f"  {divider}")


def print_iteration_summary(result: IterationResult) -> None:
    """Print a human-readable summary of an iteration."""
    divider = "=" * 60
    print(f"\n{divider}")
    print(f"  Iteration {result.iteration} Summary")
    print(divider)

    if not result.discoveries:
        print("  No new discoveries.")
    else:
        print(f"  Discoveries: {len(result.discoveries)}")
        for disc in result.discoveries:
            print(f"    [{disc.confidence.upper()}] {disc.discovery_type}: {disc.summary}")
            print(f"           {disc.artifact_type} -> {disc.artifact_path}")

    if result.artifacts_written:
        print(f"\n  Artifacts written: {len(result.artifacts_written)}")
        for path in result.artifacts_written:
            print(f"    + {path}")

    print(divider + "\n")


def print_final_report(state: OrchestratorState) -> None:
    """Print the final run report."""
    divider = "#" * 60
    print(f"\n{divider}")
    print("  COBOL Reverse Engineering -- Final Report")
    print(divider)
    print(f"  Iterations: {len(state.iterations)}")
    print(f"  Total discoveries: {state.total_discoveries}")
    print(f"  Total artifacts written: {state.total_artifacts_written}")
    print(f"  Converged: {state.is_converged()}")
    print(f"  Started: {state.started_at}")
    print(f"  Completed: {state.completed_at}")

    if state.all_artifacts_written:
        print("\n  All artifacts written:")
        for path in state.all_artifacts_written:
            print(f"    + {path}")

    print(divider + "\n")
