"""Run strategies: analysis loop, sweep, phased execution, and validation."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import yaml

from orchestrator import discover_program_files
from orchestrator.agents import (
    ALL_WORKERS,
    CROSS_CUTTING_WORKERS,
    PER_PROGRAM_WORKERS,
    run_iteration,
    run_critic_pass,
)
from orchestrator.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHUNK_THRESHOLD,
    DEFAULT_STAGING_DIR,
)
from orchestrator.models import ProgramFacts, ProgramManifest
from orchestrator.state import (
    OrchestratorState,
    print_iteration_summary,
    print_final_report,
    snapshot_output_dir,
    print_file_changes,
)
from orchestrator.stager import (
    stage_all,
    get_manifest,
    MANIFEST_FILENAME,
)
from orchestrator.tracing import (
    init_tracing,
    shutdown_tracing,
    span as trace_span,
    log_event,
    init_transcript_dir,
    set_span_attribute,
)

logger = logging.getLogger("cobol-re")


async def run_analysis_loop(
    workspace: Path,
    config: dict,
    state: OrchestratorState,
    program: str | None,
    *,
    max_iterations: int,
    n_stable: int,
    dry_run: bool,
    workers: list[str] | None = None,
    chunk_info: dict | None = None,
) -> OrchestratorState:
    """Run the convergence loop for a single program (or all programs)."""
    label = program or "all programs"
    if chunk_info:
        label = f"{program}:{chunk_info.get('chunk_id', '?')}"

    span_attrs = {"program": program or "all", "max_iterations": max_iterations}
    if chunk_info:
        span_attrs["chunk_id"] = chunk_info.get("chunk_id", "")

    remaining = max(0, max_iterations - len(state.iterations))

    with trace_span(f"analysis_loop:{label}", attributes=span_attrs):
        for _ in range(remaining):
            iteration_num = state.current_iteration
            print(f"\n--- [{label}] Iteration {iteration_num} ---")

            with trace_span(f"iteration:{label}:{iteration_num}",
                            attributes={"iteration": iteration_num}):
                result = await run_iteration(
                    workspace=workspace,
                    config=config,
                    iteration_num=iteration_num,
                    state=state,
                    dry_run=dry_run,
                    program=program,
                    workers=workers,
                    chunk_info=chunk_info,
                )

            state.record_iteration(result)
            print_iteration_summary(result)
            set_span_attribute("discoveries", len(result.discoveries))
            set_span_attribute("artifacts_written", len(result.artifacts_written))

            if state.is_converged(n_stable):
                print(f"  [{label}] Converged after {iteration_num} iterations.")
                break
        else:
            print(f"  [{label}] Reached max iterations ({max_iterations} total, {remaining} this run). Stopping.")

        state.finish_run()
    return state


def _is_program_completed(
    workspace: Path,
    config: dict,
    prog: str,
) -> bool:
    """Check whether a program has already been fully analysed (for --resume)."""
    state_file = workspace / "state" / f".cobol-re-state-{prog.lower()}.json"
    if not state_file.is_file():
        return False

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    if not data.get("completed_at"):
        return False

    output_file = Path(config["output"]) / f"business-rules/{prog.lower()}.md"
    return output_file.is_file()


async def _run_single_program(
    workspace: Path,
    config: dict,
    program: str,
    *,
    staging_dir: str,
    max_iterations: int,
    n_stable: int,
    dry_run: bool,
    resume: bool,
    workers: list[str] | None = None,
) -> tuple[str, OrchestratorState]:
    """Run analysis for a single program (used by run_sweep for parallelism)."""
    manifest = get_manifest(staging_dir, program)
    if manifest and manifest.staged and _has_br_worker(workers):
        await _run_chunked_program(
            workspace, config, program, manifest,
            staging_dir=staging_dir,
            max_iterations=max_iterations,
            n_stable=n_stable,
            dry_run=dry_run,
            resume=resume,
            workers=workers,
        )
        return program, OrchestratorState(
            workspace / "state" / f".cobol-re-state-{program.lower()}.json"
        )

    state_file = workspace / "state" / f".cobol-re-state-{program.lower()}.json"

    if resume:
        state = OrchestratorState.load(state_file)
    else:
        state = OrchestratorState(state_file)

    state.start_run()

    state = await run_analysis_loop(
        workspace,
        config,
        state,
        program,
        max_iterations=max_iterations,
        n_stable=n_stable,
        dry_run=dry_run,
        workers=workers,
    )

    return program, state


async def run_sweep(
    workspace: Path,
    config: dict,
    programs: list[str],
    *,
    max_iterations: int,
    n_stable: int,
    dry_run: bool,
    resume: bool,
    workers: list[str] | None = None,
    batch_size: int = 3,
) -> None:
    """Run one agent per program, with batch_size programs in parallel.

    batch_size controls concurrency: how many programs run simultaneously,
    each with their own agent session.  When a program has been staged
    (manifest exists), its chunks are processed sequentially within its
    own agent.
    """
    settings = config.get("settings", {})
    staging_dir = settings.get("staging_dir", DEFAULT_STAGING_DIR)

    remaining: list[str] = []
    skipped = 0

    for prog in programs:
        if resume and _is_program_completed(workspace, config, prog):
            skipped += 1
            logger.info("Skipping %s (already completed)", prog)
        else:
            remaining.append(prog)

    if skipped:
        print(f"  Skipped {skipped} already-completed programs")

    program_states: list[tuple[str, OrchestratorState]] = []
    total_windows = (len(remaining) + batch_size - 1) // batch_size

    for window_start in range(0, len(remaining), batch_size):
        window = remaining[window_start : window_start + batch_size]
        window_idx = window_start // batch_size + 1

        print(f"\n{'#' * 60}")
        print(
            f"  Parallel window {window_idx}/{total_windows}"
            f"  ({len(window)} programs): {', '.join(window)}"
        )
        print(f"{'#' * 60}")

        results = await asyncio.gather(
            *(
                _run_single_program(
                    workspace,
                    config,
                    prog,
                    staging_dir=staging_dir,
                    max_iterations=max_iterations,
                    n_stable=n_stable,
                    dry_run=dry_run,
                    resume=resume,
                    workers=workers,
                )
                for prog in window
            )
        )

        for prog, state in results:
            program_states.append((prog, state))

    _print_sweep_summary(program_states, skipped=skipped)


def _has_br_worker(workers: list[str] | None) -> bool:
    """Check if business-rules is in the active worker list."""
    if workers is None:
        return True
    return "business-rules" in workers


async def _run_chunked_program(
    workspace: Path,
    config: dict,
    program: str,
    manifest: ProgramManifest,
    *,
    staging_dir: str,
    max_iterations: int,
    n_stable: int,
    dry_run: bool,
    resume: bool,
    workers: list[str] | None = None,
) -> None:
    """Run chunk-level analysis for a staged program.

    Iterates over each chunk in the manifest, runs the business-rules worker
    with chunk-specific context, then merges outputs and validates coverage.
    """
    prog_slug = program.lower()
    prog_staging = Path(staging_dir) / prog_slug
    source_path = manifest.source_path
    data_div_path = str(prog_staging / "data-division.cbl")
    manifest_path = str(prog_staging / MANIFEST_FILENAME)

    non_br_workers = [w for w in (workers or list(PER_PROGRAM_WORKERS)) if w != "business-rules"]
    if non_br_workers:
        state_file = workspace / "state" / f".cobol-re-state-{prog_slug}-data.json"
        state = OrchestratorState(state_file) if not resume else OrchestratorState.load(state_file)
        if resume and state.is_completed:
            logger.info("Data workers for %s already completed — skipping", program)
        else:
            state.start_run()
            await run_analysis_loop(
                workspace, config, state, program,
                max_iterations=max_iterations,
                n_stable=n_stable,
                dry_run=dry_run,
                workers=non_br_workers,
            )
            print_final_report(state)

    chunk_count = len(manifest.chunks)
    output_dir = Path(config["output"])
    output_file_path = str(output_dir / "business-rules" / f"{prog_slug}.md")
    print(f"\n  Chunked analysis: {chunk_count} chunks for {program}")

    for ci, chunk in enumerate(manifest.chunks, 1):
        chunk_path = str(prog_staging / f"chunk-{chunk.chunk_id}.cbl")
        print(f"\n  --- Chunk {ci}/{chunk_count}: {chunk.chunk_id} "
              f"({len(chunk.paragraphs)} paragraphs, [{chunk.classification}]) ---")

        state_file = workspace / "state" / f".cobol-re-state-{prog_slug}-{chunk.chunk_id}.json"
        if resume:
            state = OrchestratorState.load(state_file)
        else:
            state = OrchestratorState(state_file)

        if resume and state.is_completed:
            logger.info("Chunk %s for %s already completed — skipping", chunk.chunk_id, program)
            print(f"  Chunk {chunk.chunk_id} already completed (resume). Skipping.")
            continue

        state.start_run()

        ci_info = {
            "chunk_path": chunk_path,
            "chunk_id": chunk.chunk_id,
            "data_div_path": data_div_path,
            "manifest_path": manifest_path,
            "source_path": source_path,
            "output_file_path": output_file_path,
        }

        await run_analysis_loop(
            workspace, config, state, program,
            max_iterations=1,
            n_stable=n_stable,
            dry_run=dry_run,
            workers=["business-rules"],
            chunk_info=ci_info,
        )
        print_final_report(state)

    if not dry_run:
        validate_coverage(config, program, manifest)
        if manifest.facts:
            from orchestrator.validator import validate_business_rules
            cross_facts_path = Path(staging_dir) / "program-facts.yaml"
            called_by: list[str] = []
            if cross_facts_path.is_file():
                try:
                    cf = yaml.safe_load(cross_facts_path.read_text(encoding="utf-8")) or {}
                    called_by = cf.get("called_by", {}).get(program.upper(), [])
                except (yaml.YAMLError, OSError):
                    pass
            vr = validate_business_rules(
                Path(output_file_path), manifest.facts, called_by=called_by,
            )
            if vr.frontmatter_repairs:
                print(f"  Restored {len(vr.frontmatter_repairs)} frontmatter fields")
            if vr.incomplete_sections:
                print(f"  Incomplete sections: {', '.join(vr.incomplete_sections)}")


def _print_sweep_summary(
    program_states: list[tuple[str, OrchestratorState]],
    *,
    skipped: int = 0,
) -> None:
    """Print a combined summary after a sweep completes."""
    divider = "#" * 60
    total_disc = sum(s.total_discoveries for _, s in program_states)
    total_arts = sum(s.total_artifacts_written for _, s in program_states)

    print(f"\n{divider}")
    print("  SWEEP COMPLETE -- Combined Summary")
    print(divider)
    print(f"  Programs processed:    {len(program_states)}")
    if skipped:
        print(f"  Programs skipped:      {skipped} (already completed)")
    print(f"  Total discoveries:     {total_disc}")
    print(f"  Total artifacts written: {total_arts}")
    print()
    print(f"  {'Program':<35} {'Disc':>6} {'Arts':>6} {'Converged':>10}")
    print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*10}")
    for prog, state in program_states:
        converged_str = "yes" if state.is_converged() else "no"
        print(
            f"  {prog:<35} {state.total_discoveries:>6} "
            f"{state.total_artifacts_written:>6} {converged_str:>10}"
        )
    print(f"\n  {'TOTAL':<35} {total_disc:>6} {total_arts:>6}")
    print(divider + "\n")


def validate_coverage(
    config: dict,
    program: str,
    manifest: ProgramManifest,
) -> float:
    """Check that every HIGH-priority paragraph has rules in the merged output.

    Returns coverage as a percentage (0.0--100.0).
    """
    output_dir = Path(config["output"])
    merged_path = output_dir / f"business-rules/{program.lower()}.md"

    if not merged_path.is_file():
        print(f"  Coverage: {program} -- merged file not found")
        return 0.0

    content = merged_path.read_text(encoding="utf-8").upper()

    high_paragraphs = [
        p.name for p in manifest.paragraphs if p.priority == "HIGH"
    ]
    if not high_paragraphs:
        return 100.0

    covered = [p for p in high_paragraphs if p.upper() in content]
    uncovered = [p for p in high_paragraphs if p.upper() not in content]
    coverage = len(covered) / len(high_paragraphs) * 100

    divider = "-" * 40
    print(f"\n  {divider}")
    print(f"  Coverage for {program}: {coverage:.1f}%")
    print(f"  HIGH paragraphs: {len(high_paragraphs)}, "
          f"covered: {len(covered)}, missing: {len(uncovered)}")

    if uncovered:
        print("  Missing paragraphs:")
        for p in uncovered:
            print(f"    - {p}")

    print(f"  {divider}")
    return coverage


def _validate_phase1_outputs(config: dict) -> bool:
    """Deterministic validation of Phase 1 outputs.

    Checks file structure, frontmatter schema, section completeness, and
    removes stray files from the output root.  Returns True if all expected
    files are present and valid.
    """
    from orchestrator.validator import (
        validate_phase1_outputs,
        cleanup_stray_files,
    )

    output_dir = Path(config["output"])
    divider = "-" * 40
    print(f"\n  {divider}")
    print("  Phase 1 output validation")
    print(f"  {divider}")

    deleted = cleanup_stray_files(output_dir)
    for name in deleted:
        print(f"  DELETED stray: {name}")

    results = validate_phase1_outputs(output_dir)
    all_ok = True

    for vr in results:
        rel_path = str(Path(vr.path).relative_to(output_dir))
        if vr.passed:
            size = Path(vr.path).stat().st_size
            print(f"  OK: {rel_path} ({size:,} bytes)")
        else:
            all_ok = False
            issues = vr.frontmatter_repairs + vr.incomplete_sections
            print(f"  ISSUE: {rel_path} -- {', '.join(issues)}")

    if all_ok and not deleted:
        print("  All Phase 1 outputs present and valid.")
    elif all_ok and deleted:
        print(f"  Phase 1 outputs valid after removing {len(deleted)} stray file(s).")
    else:
        print("  WARNING: Some Phase 1 outputs are missing or incomplete.")
        print("  Phase 2 workers may produce lower-quality results.")

    print(f"  {divider}")
    return all_ok


def _validate_phase4_outputs(config: dict) -> bool:
    """Deterministic validation of Phase 4 test-specification outputs.

    Checks frontmatter, section completeness, auto-corrects the coverage
    summary, and warns on capability gaps.  Returns True if all files valid.
    """
    from orchestrator.validator import validate_test_specs_outputs

    output_dir = Path(config["output"])
    divider = "-" * 40
    print(f"\n  {divider}")
    print("  Phase 4 output validation")
    print(f"  {divider}")

    results = validate_test_specs_outputs(output_dir)
    all_ok = True

    for vr in results:
        try:
            rel_path = str(Path(vr.path).relative_to(output_dir))
        except ValueError:
            rel_path = vr.path

        if vr.passed:
            if Path(vr.path).is_file():
                size = Path(vr.path).stat().st_size
                print(f"  OK: {rel_path} ({size:,} bytes)")
        else:
            all_ok = False
            issues = vr.frontmatter_repairs + vr.incomplete_sections
            print(f"  ISSUE: {rel_path} -- {', '.join(issues)}")

    if all_ok:
        print("  All Phase 4 outputs present and valid.")
    else:
        print("  WARNING: Some Phase 4 outputs have issues.")

    print(f"  {divider}")
    return all_ok


def _discover_programs(config: dict) -> list[str]:
    """Scan source program directories for COBOL program files."""
    files = discover_program_files(config)
    programs = [f.stem.upper() for f in files]

    if not programs:
        program_dirs = config["source"].get("programs", [])
        extensions = config["source"].get("extensions", {}).get(
            "programs", [".cbl", ".cob", ".CBL", ".COB"]
        )
        dirs_str = ", ".join(program_dirs) or "(none configured)"
        print("ERROR: No COBOL program files found.", file=sys.stderr)
        print(f"  Searched: {dirs_str}", file=sys.stderr)
        print(f"  Extensions: {extensions}", file=sys.stderr)
        sys.exit(1)

    return programs


def _select_strategy(config: dict) -> str:
    """Select the optimal run strategy based on codebase size.

    Returns "default" (<= 10 programs, all-at-once) or "phased" (3-phase).
    """
    strategy_setting = config.get("settings", {}).get("strategy", "auto")
    if strategy_setting in ("default", "phased"):
        return strategy_setting

    programs = _discover_programs(config)
    count = len(programs)

    if count <= 10:
        logger.info("Auto-strategy: %d programs -> default mode", count)
        return "default"
    else:
        logger.info("Auto-strategy: %d programs -> phased mode", count)
        return "phased"


async def run_phased(
    workspace: Path,
    config: dict,
    programs: list[str],
    *,
    max_iterations: int,
    n_stable: int,
    dry_run: bool,
    resume: bool,
    batch_size: int,
    print_banner_fn: object = None,
) -> None:
    """Run the five-phase analysis strategy for optimal speed and accuracy."""
    phase_divider = "=" * 60

    init_tracing(workspace, config)
    init_transcript_dir(str(workspace))

    if print_banner_fn:
        print_banner_fn(
            config, strategy="phased", programs=programs,
            max_iterations=max_iterations, dry_run=dry_run, batch_size=batch_size,
        )

    output_dir = Path(config["output"])

    with trace_span("phased_run", attributes={
        "programs": len(programs), "batch_size": batch_size,
    }):
        # --- Phase 1: Cross-cutting ---
        print(f"\n{phase_divider}")
        print("  PHASE 1: Cross-cutting analysis")
        print(phase_divider)

        state_file = workspace / "state" / ".cobol-re-state-phase1.json"
        if resume:
            state = OrchestratorState.load(state_file)
        else:
            state = OrchestratorState(state_file)

        if resume and state.is_completed:
            logger.info("Phase 1 already completed — skipping")
            print("  Phase 1 already completed (resume). Skipping.")
            log_event("phase_skipped", phase="phase1", reason="already_completed")
        else:
            with trace_span("phase1:cross_cutting"):
                snap_before = snapshot_output_dir(output_dir)
                state.start_run()

                await run_analysis_loop(
                    workspace,
                    config,
                    state,
                    None,
                    max_iterations=max_iterations,
                    n_stable=n_stable,
                    dry_run=dry_run,
                    workers=list(CROSS_CUTTING_WORKERS),
                )

                snap_after = snapshot_output_dir(output_dir)
                print_file_changes("Phase 1 workers", output_dir, snap_before, snap_after)
                print_final_report(state)

                if not dry_run:
                    _validate_phase1_outputs(config)
                    snap_before_critic = snapshot_output_dir(output_dir)
                    await run_critic_pass(workspace, config, phase="phase1")
                    snap_after_critic = snapshot_output_dir(output_dir)
                    print_file_changes("Phase 1 critic", output_dir, snap_before_critic, snap_after_critic)

        # --- Phase 2: Per-program sweep ---
        print(f"\n{phase_divider}")
        print("  PHASE 2: Per-program analysis")
        print(phase_divider)

        with trace_span("phase2:per_program", attributes={"programs": len(programs)}):
            snap_before = snapshot_output_dir(output_dir)

            await run_sweep(
                workspace,
                config,
                programs,
                max_iterations=max_iterations,
                n_stable=n_stable,
                dry_run=dry_run,
                resume=resume,
                workers=list(PER_PROGRAM_WORKERS),
                batch_size=batch_size,
            )

            snap_after = snapshot_output_dir(output_dir)
            print_file_changes("Phase 2 workers", output_dir, snap_before, snap_after)

        # --- Phase 3: Synthesis ---
        print(f"\n{phase_divider}")
        print("  PHASE 3: Synthesis")
        print(phase_divider)

        state_file = workspace / "state" / ".cobol-re-state-phase3.json"
        if resume:
            state = OrchestratorState.load(state_file)
        else:
            state = OrchestratorState(state_file)

        if resume and state.is_completed:
            logger.info("Phase 3 already completed — skipping")
            print("  Phase 3 already completed (resume). Skipping.")
            log_event("phase_skipped", phase="phase3", reason="already_completed")
        else:
            with trace_span("phase3:synthesis"):
                state.start_run()

                await run_analysis_loop(
                    workspace,
                    config,
                    state,
                    None,
                    max_iterations=max_iterations,
                    n_stable=n_stable,
                    dry_run=dry_run,
                    workers=["requirements"],
                )

                print_final_report(state)

        # --- Phase 4: Test Specifications ---
        print(f"\n{phase_divider}")
        print("  PHASE 4: Test Specifications")
        print(phase_divider)

        state_file = workspace / "state" / ".cobol-re-state-phase4.json"
        if resume:
            state = OrchestratorState.load(state_file)
        else:
            state = OrchestratorState(state_file)

        if resume and state.is_completed:
            logger.info("Phase 4 already completed — skipping")
            print("  Phase 4 already completed (resume). Skipping.")
            log_event("phase_skipped", phase="phase4", reason="already_completed")
        else:
            with trace_span("phase4:test_specs"):
                state.start_run()

                await run_analysis_loop(
                    workspace,
                    config,
                    state,
                    None,
                    max_iterations=max_iterations,
                    n_stable=n_stable,
                    dry_run=dry_run,
                    workers=["test-specs"],
                )

                print_final_report(state)

                if not dry_run:
                    _validate_phase4_outputs(config)
                    snap_before_critic = snapshot_output_dir(output_dir)
                    await run_critic_pass(workspace, config, phase="phase4")
                    snap_after_critic = snapshot_output_dir(output_dir)
                    print_file_changes(
                        "Phase 4 critic", output_dir,
                        snap_before_critic, snap_after_critic,
                    )

        # --- Phase 5: Implementation Plan ---
        print(f"\n{phase_divider}")
        print("  PHASE 5: Implementation Plan")
        print(phase_divider)

        state_file = workspace / "state" / ".cobol-re-state-phase5.json"
        if resume:
            state = OrchestratorState.load(state_file)
        else:
            state = OrchestratorState(state_file)

        if resume and state.is_completed:
            logger.info("Phase 5 already completed — skipping")
            print("  Phase 5 already completed (resume). Skipping.")
            log_event("phase_skipped", phase="phase5", reason="already_completed")
        else:
            with trace_span("phase5:implementation_plan"):
                state.start_run()

                await run_analysis_loop(
                    workspace,
                    config,
                    state,
                    None,
                    max_iterations=max_iterations,
                    n_stable=n_stable,
                    dry_run=dry_run,
                    workers=["implementation-plan"],
                )

                print_final_report(state)

    shutdown_tracing()

    print(f"\n{'#' * 60}")
    print("  ALL PHASES COMPLETE")
    print(f"{'#' * 60}\n")
