"""Orchestrator prompt and its helper builders."""

from __future__ import annotations

from ._helpers import _batch_scope_note


ORCHESTRATOR_PROMPT = """\
You are the COBOL Reverse Engineering Orchestrator.
This is iteration {iteration} of the convergence loop.
{program_instruction}

Application: {application_name}

{source_context}

Your task:
1. Spawn these worker subagents IN PARALLEL using the Task tool:
{worker_list}
   Each worker will return a JSON array of discovery objects.

2. Collect all discovery arrays from the workers and merge them into a single list.
   Deduplicate by (discovery_type, artifact_type, artifact_path).

{requirements_instruction}

{test_specs_instruction}

{impl_plan_instruction}

{result_step}. Return a final JSON summary with exactly this structure (no markdown fences):
   {{"discoveries": [...array of discovery objects...], "artifacts_written": [...array of file paths written...]}}

{dry_run_instruction}

{previous_context}

IMPORTANT: Return ONLY the final JSON summary. No other text."""


def build_worker_list_prompt(workers: list[str], worker_agent_map: dict[str, str]) -> str:
    """Build the numbered worker list for the orchestrator prompt."""
    lines = []
    for i, w in enumerate(workers, 1):
        agent_key = worker_agent_map[w]
        lines.append(f"   {i}. {agent_key}")
    return "\n".join(lines)


def build_dry_run_instruction(dry_run: bool) -> str:
    if dry_run:
        return (
            "DRY RUN MODE: Do NOT create any files. Instead, in artifacts_written, "
            "list the file paths that WOULD be created."
        )
    return ""


def build_program_instruction(
    program: str | None = None,
    programs: list[str] | None = None,
) -> str:
    if programs and len(programs) > 1:
        return _batch_scope_note(programs)
    if program:
        return (
            f"\nSCOPED RUN: You are only analysing program **{program}**. "
            f"All discoveries must relate to {program}. You may read other programs "
            f"for context (e.g. to understand call relationships)."
        )
    return ""


def build_previous_context(state) -> str:
    """Build the previously-written-artifacts block for the orchestrator.

    Accepts an OrchestratorState (imported by the caller) to avoid a
    circular dependency between this prompt module and orchestrator.
    """
    if not state.all_artifacts_written:
        return ""
    paths_list = "\n".join(f"  - {p}" for p in state.all_artifacts_written[-50:])
    return (
        f"## Previously Written Artifacts ({state.total_artifacts_written} total)\n\n"
        f"These already exist. Update them if you find new information, but do "
        f"not re-create from scratch:\n"
        f"{paths_list}"
    )
