"""CLI argument parsing, command handlers, and main entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from orchestrator import discover_program_files
from orchestrator.agents import ALL_WORKERS
from orchestrator.config import (
    SCRIPT_DIR,
    CONFIG_FILENAME,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_N_STABLE,
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHUNK_THRESHOLD,
    DEFAULT_STAGING_DIR,
    load_config,
    resolve_paths,
    find_workspace,
    cmd_init,
)
from orchestrator.models import ProgramFacts, ProgramManifest
from orchestrator.runner import (
    run_analysis_loop,
    run_phased,
    _discover_programs,
    _select_strategy,
)
from orchestrator.state import (
    OrchestratorState,
    print_final_report,
)
from orchestrator.stager import (
    stage_all,
    stage_program,
    get_manifest,
    MANIFEST_FILENAME,
)
from orchestrator.tracing import (
    init_tracing,
    shutdown_tracing,
    init_transcript_dir,
)

logger = logging.getLogger("cobol-re")


def cmd_stage(args: argparse.Namespace) -> None:
    """Stage large COBOL programs into chunks for agent analysis."""
    if args.workspace:
        workspace = Path(args.workspace).resolve()
    else:
        workspace = find_workspace()

    config = load_config(workspace)
    config = resolve_paths(config, workspace)

    settings = config.get("settings", {})
    staging_dir = settings.get("staging_dir", DEFAULT_STAGING_DIR)
    chunk_threshold = args.chunk_threshold or settings.get(
        "chunk_threshold", DEFAULT_CHUNK_THRESHOLD
    )

    divider = "=" * 60
    print(f"\n{divider}")
    print("  COBOL Staging Pipeline")
    print(f"  Application: {config.get('application', 'Unknown')}")
    print(f"  Staging dir: {staging_dir}")
    print(f"  Chunk threshold: {chunk_threshold} lines")
    print(divider + "\n")

    if args.program:
        program = args.program.upper()
        source_file = _find_program_source(config, program)
        if not source_file:
            print(f"ERROR: Could not find source file for {program}", file=sys.stderr)
            sys.exit(1)

        manifest = stage_program(source_file, staging_dir, chunk_threshold)
        _print_staging_summary([manifest])
    else:
        manifests = stage_all(config, staging_dir, chunk_threshold)
        _print_staging_summary(manifests)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate output artifacts against extracted ProgramFacts."""
    if args.workspace:
        workspace = Path(args.workspace).resolve()
    else:
        workspace = find_workspace()

    config = load_config(workspace)
    config = resolve_paths(config, workspace)

    settings = config.get("settings", {})
    staging_dir = Path(settings.get("staging_dir", DEFAULT_STAGING_DIR))
    output_dir = Path(config["output"])

    cross_facts_path = staging_dir / "program-facts.yaml"
    called_by_map: dict[str, list[str]] = {}
    if cross_facts_path.is_file():
        try:
            cf = yaml.safe_load(cross_facts_path.read_text(encoding="utf-8")) or {}
            called_by_map = cf.get("called_by", {})
        except (yaml.YAMLError, OSError):
            pass

    facts_by_program: dict[str, ProgramFacts] = {}
    if staging_dir.is_dir():
        for prog_dir in staging_dir.iterdir():
            if not prog_dir.is_dir():
                continue
            manifest = get_manifest(staging_dir, prog_dir.name)
            if manifest and manifest.facts:
                facts_by_program[manifest.program] = manifest.facts

    if not facts_by_program:
        print("No program facts found. Run staging first.")
        return

    from orchestrator.validator import validate_all_business_rules
    results = validate_all_business_rules(output_dir, facts_by_program, called_by_map)

    divider = "=" * 60
    print(f"\n{divider}")
    print("  Artifact Validation Results")
    print(divider)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    repairs = sum(len(r.frontmatter_repairs) for r in results)
    incomplete = sum(len(r.incomplete_sections) for r in results)

    print(f"  Files checked:       {len(results)}")
    print(f"  Passed:              {passed}")
    print(f"  Failed:              {failed}")
    print(f"  Frontmatter repairs: {repairs}")
    print(f"  Incomplete sections: {incomplete}")

    if failed:
        print(f"\n  {'File':<40} {'Repairs':>8} {'Incomplete':>10}")
        print(f"  {'-'*40} {'-'*8} {'-'*10}")
        for r in results:
            if not r.passed:
                fname = Path(r.path).name
                print(
                    f"  {fname:<40} {len(r.frontmatter_repairs):>8} "
                    f"{len(r.incomplete_sections):>10}"
                )

    print(divider + "\n")


def _find_program_source(config: dict, program: str) -> str | None:
    """Find the source file path for a program name."""
    for f in discover_program_files(config):
        if f.stem.upper() == program:
            return str(f)
    return None


def _print_staging_summary(manifests: list[ProgramManifest]) -> None:
    """Print summary of staging results."""
    divider = "=" * 60
    print(f"\n{divider}")
    print("  Staging Summary")
    print(divider)

    if not manifests:
        print("  No programs staged.")
        print(divider + "\n")
        return

    print(f"\n  {'Program':<20} {'LOC':>6} {'Paragraphs':>12} {'Chunks':>8}")
    print(f"  {'-'*20} {'-'*6} {'-'*12} {'-'*8}")
    for m in manifests:
        print(
            f"  {m.program:<20} {m.loc:>6} {len(m.paragraphs):>12} {len(m.chunks):>8}"
        )
        for c in m.chunks:
            para_count = len(c.paragraphs)
            lines = c.end_line - c.start_line + 1
            print(
                f"    chunk-{c.chunk_id:<16} {lines:>5} lines  "
                f"{para_count:>3} paragraphs  [{c.classification}]"
            )

    print(f"\n  Total: {len(manifests)} program(s) staged")
    print(divider + "\n")


def _parse_workers(value: str) -> list[str]:
    """Parse and validate a comma-separated worker list."""
    valid = set(ALL_WORKERS) | {"requirements", "test-specs", "implementation-plan"}
    workers = [w.strip() for w in value.split(",")]
    invalid = [w for w in workers if w not in valid]
    if invalid:
        print(
            f"ERROR: Unknown workers: {', '.join(invalid)}\n"
            f"  Valid workers: {', '.join(sorted(valid))}",
            file=sys.stderr,
        )
        sys.exit(1)
    return workers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="COBOL Reverse Engineering Agent (Claude Agent SDK)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    init_parser = subparsers.add_parser("init", help="Scaffold a new workspace")
    init_parser.add_argument(
        "--workspace", type=str, default=None,
        help="Path to create workspace at (default: ./workspace/ subdirectory)",
    )

    stage_parser = subparsers.add_parser(
        "stage", help="Stage large COBOL programs into chunks for analysis"
    )
    stage_parser.add_argument(
        "--program", type=str, default=None,
        help="Stage a single program (e.g. ACCT0100)",
    )
    stage_parser.add_argument(
        "--chunk-threshold", type=int, default=None,
        help=f"Line count above which a program gets chunked (default: {DEFAULT_CHUNK_THRESHOLD})",
    )
    stage_parser.add_argument(
        "--workspace", type=str, default=None,
        help="Path to workspace directory (default: current directory)",
    )
    stage_parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )

    run_parser = subparsers.add_parser("run", help="Run the analysis")

    run_parser.add_argument(
        "--program", type=str, default=None,
        help="Analyse a single program (e.g. ACCT0100)",
    )
    run_parser.add_argument(
        "--workers", type=str, default=None,
        help="Comma-separated list of workers to run "
             "(inventory,data,business-rules,flow,integration,requirements,test-specs,implementation-plan)",
    )
    run_parser.add_argument(
        "--batch-size", type=int, default=None,
        help=f"Max programs to analyse in parallel (default: {DEFAULT_BATCH_SIZE})",
    )
    run_parser.add_argument(
        "--dry-run", action="store_true",
        help="Report discoveries without writing artifact files",
    )
    run_parser.add_argument(
        "--max-iterations", type=int, default=None,
        help=f"Maximum iterations (default: from config or {DEFAULT_MAX_ITERATIONS})",
    )
    run_parser.add_argument(
        "--n-stable", type=int, default=None,
        help=f"Stop after N consecutive empty iterations "
             f"(default: from config or {DEFAULT_N_STABLE})",
    )
    run_parser.add_argument(
        "--resume", action="store_true",
        help="Resume from previous run state (skips completed programs)",
    )
    run_parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )
    run_parser.add_argument(
        "--workspace", type=str, default=None,
        help="Path to workspace directory (default: current directory)",
    )

    validate_parser = subparsers.add_parser(
        "validate", help="Validate output artifacts against extracted facts"
    )
    validate_parser.add_argument(
        "--workspace", type=str, default=None,
        help="Path to workspace directory (default: current directory)",
    )
    validate_parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    return args


def _print_banner(
    config: dict,
    *,
    strategy: str | None = None,
    program: str | None = None,
    programs: list[str] | None = None,
    workers: list[str] | None = None,
    max_iterations: int = 1,
    dry_run: bool = False,
    batch_size: int | None = None,
) -> None:
    """Print a consistent startup banner."""
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    model = config.get("settings", {}).get("model", "default")
    divider = "=" * 60

    print(f"\n{divider}")
    print("  COBOL Reverse Engineering Agent")
    print(f"  Application: {config.get('application', 'Unknown')}")
    print(f"  Model: {model}")
    print(f"  Endpoint: {base_url or 'api.anthropic.com (direct)'}")

    if program:
        print(f"  Program: {program}")
    elif programs:
        count = len(programs)
        preview = ", ".join(programs[:10])
        if count > 10:
            preview += f"... (+{count - 10} more)"
        print(f"  Programs ({count}): {preview}")

    if strategy:
        print(f"  Strategy: {strategy}")

    print(f"  Workers: {', '.join(workers) if workers else 'all'}")

    if batch_size and batch_size > 1:
        print(f"  Parallelism: {batch_size} programs")

    print(f"  Max iterations: {max_iterations}")
    print(f"  Dry run: {dry_run}")
    print(divider + "\n")


async def main() -> None:
    args = parse_args()

    if args.command == "init":
        target = Path(args.workspace).resolve() if args.workspace else SCRIPT_DIR
        cmd_init(target)
        return

    load_dotenv()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "stage":
        cmd_stage(args)
        return

    if args.command == "validate":
        cmd_validate(args)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY environment variable is required.\n"
            "  Direct API:  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  AI Gateway:  export ANTHROPIC_BASE_URL=https://your-gateway/...\n"
            "               export ANTHROPIC_API_KEY=<jwt-or-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.workspace:
        workspace = Path(args.workspace).resolve()
    else:
        workspace = find_workspace()

    config = load_config(workspace)
    config = resolve_paths(config, workspace)

    settings = config.get("settings", {})
    max_iterations = args.max_iterations or settings.get(
        "max_iterations", DEFAULT_MAX_ITERATIONS
    )
    n_stable = args.n_stable or settings.get("n_stable", DEFAULT_N_STABLE)
    batch_size = args.batch_size or settings.get("batch_size", DEFAULT_BATCH_SIZE)
    workers = _parse_workers(args.workers) if args.workers else None

    staging_dir = settings.get("staging_dir", DEFAULT_STAGING_DIR)
    chunk_threshold = settings.get("chunk_threshold", DEFAULT_CHUNK_THRESHOLD)
    staged = stage_all(config, staging_dir, chunk_threshold)
    if staged:
        _print_staging_summary(staged)

    if args.program:
        program = args.program.upper()

        state_file = workspace / "state" / ".cobol-re-state.json"
        state = OrchestratorState.load(state_file) if args.resume else OrchestratorState(state_file)
        state.start_run()

        init_tracing(workspace, config)
        init_transcript_dir(str(workspace))

        _print_banner(
            config, program=program, workers=workers,
            max_iterations=max_iterations, dry_run=args.dry_run,
        )

        await run_analysis_loop(
            workspace, config, state, program,
            max_iterations=max_iterations,
            n_stable=n_stable,
            dry_run=args.dry_run,
            workers=workers,
        )

        print_final_report(state)
        shutdown_tracing()
        return

    strategy = _select_strategy(config)
    programs = _discover_programs(config)

    if workers:
        strategy = "default"

    if strategy == "default":
        state_file = workspace / "state" / ".cobol-re-state.json"
        state = OrchestratorState.load(state_file) if args.resume else OrchestratorState(state_file)
        state.start_run()

        init_tracing(workspace, config)
        init_transcript_dir(str(workspace))

        _print_banner(
            config, strategy="default", programs=programs, workers=workers,
            max_iterations=max_iterations, dry_run=args.dry_run,
        )

        await run_analysis_loop(
            workspace, config, state, None,
            max_iterations=max_iterations,
            n_stable=n_stable,
            dry_run=args.dry_run,
            workers=workers,
        )

        print_final_report(state)
        shutdown_tracing()

    else:
        await run_phased(
            workspace, config, programs,
            max_iterations=max_iterations,
            n_stable=n_stable,
            dry_run=args.dry_run,
            resume=args.resume,
            batch_size=batch_size,
            print_banner_fn=_print_banner,
        )
