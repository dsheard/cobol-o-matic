"""Agent construction, SDK interaction, response parsing, and critic pass."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

from orchestrator.models import Discovery, IterationResult
from orchestrator.state import OrchestratorState
from orchestrator.tracing import (
    log_event,
    capture_session_transcript,
    span as trace_span,
)
from prompts import (
    build_inventory_worker_prompt,
    build_data_worker_prompt,
    build_business_rules_worker_prompt,
    build_flow_worker_prompt,
    build_integration_worker_prompt,
    build_requirements_prompt,
    build_test_specs_prompt,
    build_implementation_plan_prompt,
    ORCHESTRATOR_PROMPT,
    build_worker_list_prompt,
    build_dry_run_instruction,
    build_program_instruction,
    build_previous_context,
    source_context,
)

logger = logging.getLogger("cobol-re")

ALL_WORKERS = ("inventory", "data", "business-rules", "flow", "integration")
CROSS_CUTTING_WORKERS = ("inventory", "flow", "integration", "data")
PER_PROGRAM_WORKERS = ("business-rules",)

WORKER_AGENT_MAP = {
    "inventory": "inventory-worker",
    "data": "data-worker",
    "business-rules": "business-rules-worker",
    "flow": "flow-worker",
    "integration": "integration-worker",
    "requirements": "requirements-deriver",
    "test-specs": "test-specs-deriver",
    "implementation-plan": "implementation-plan-deriver",
}

WORKER_PROMPT_BUILDERS = {
    "inventory": build_inventory_worker_prompt,
    "data": build_data_worker_prompt,
    "business-rules": build_business_rules_worker_prompt,
    "flow": build_flow_worker_prompt,
    "integration": build_integration_worker_prompt,
    "requirements": build_requirements_prompt,
    "test-specs": build_test_specs_prompt,
    "implementation-plan": build_implementation_plan_prompt,
}

WORKER_DESCRIPTIONS = {
    "inventory": "Catalogs COBOL programs, copybooks, and JCL jobs",
    "data": "Extracts data structures, file layouts, and DB operations",
    "business-rules": "Extracts business rules and dependency graph from PROCEDURE DIVISION",
    "flow": "Traces call chains, batch flows, and data flows",
    "integration": "Maps external interfaces, I/O, messaging, and system boundaries",
    "requirements": "Derives functional capabilities and modernization notes",
    "test-specs": "Derives stack-agnostic test specifications from business rules and requirements",
    "implementation-plan": "Derives a phased migration plan with strategy selection from capabilities and dependencies",
}


def _extract_json_from_result(text: str) -> dict | None:
    """Extract JSON object from agent result text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    match = re.search(
        r'\{[\s\S]*"discoveries"[\s\S]*"artifacts_written"[\s\S]*\}', text
    )
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error("Could not parse agent result as JSON:\n%s", text[:500])
        return None


def _parse_iteration_result(text: str, iteration: int) -> IterationResult:
    """Parse the agent's JSON summary into an IterationResult."""
    data = _extract_json_from_result(text)
    if not data:
        return IterationResult(iteration=iteration)

    discoveries = []
    for d in data.get("discoveries", []):
        try:
            discoveries.append(Discovery.from_dict(d))
        except (TypeError, KeyError) as e:
            logger.warning("Skipping malformed discovery: %s", e)

    return IterationResult(
        iteration=iteration,
        discoveries=discoveries,
        artifacts_written=data.get("artifacts_written", []),
    )


def _build_agents(
    config: dict,
    program: str | None = None,
    workers: list[str] | None = None,
    chunk_info: dict | None = None,
    workspace: Path | None = None,
) -> dict[str, AgentDefinition]:
    """Define the worker subagents, filtered by active workers.

    When *chunk_info* is provided, the business-rules worker prompt is built
    with chunk-specific paths (chunk_path, data_div_path, manifest_path,
    source_path, chunk_id).

    When *workspace* is provided, each prompt builder receives it so it can
    check for existing draft output files and inject draft-aware instructions.
    """
    write_tools = ["Read", "Write", "Glob", "Grep", "Skill"]
    scope_label = f" (scoped to {program})" if program else ""

    active_workers = workers or list(ALL_WORKERS)

    agents: dict[str, AgentDefinition] = {}

    output_dir = config.get("output", "./output")

    for worker_name in active_workers:
        agent_key = WORKER_AGENT_MAP.get(worker_name)
        prompt_builder = WORKER_PROMPT_BUILDERS.get(worker_name)
        description = WORKER_DESCRIPTIONS.get(worker_name, "")
        if agent_key and prompt_builder:
            if worker_name == "business-rules" and chunk_info:
                prompt = prompt_builder(config, program, **chunk_info,
                                        workspace=workspace)
            elif worker_name == "business-rules" and program:
                prog_slug = program.lower()
                ofp = f"{output_dir}/business-rules/{prog_slug}.md"
                prompt = prompt_builder(config, program, output_file_path=ofp,
                                        workspace=workspace)
            else:
                prompt = prompt_builder(config, program, workspace=workspace)
            agents[agent_key] = AgentDefinition(
                description=f"{description}{scope_label}.",
                prompt=prompt,
                tools=write_tools,
            )

    if not workers or "requirements" in workers:
        agents["requirements-deriver"] = AgentDefinition(
            description="Synthesizes all analysis outputs into capabilities and modernization notes.",
            prompt=build_requirements_prompt(config, workspace=workspace),
            tools=write_tools,
        )

    if not workers or "test-specs" in workers:
        agents["test-specs-deriver"] = AgentDefinition(
            description="Derives stack-agnostic test specifications from business rules and requirements.",
            prompt=build_test_specs_prompt(config, workspace=workspace),
            tools=write_tools,
        )

    if not workers or "implementation-plan" in workers:
        agents["implementation-plan-deriver"] = AgentDefinition(
            description="Derives a phased migration plan with strategy selection from capabilities and dependencies.",
            prompt=build_implementation_plan_prompt(config, workspace=workspace),
            tools=write_tools,
        )

    return agents


async def run_iteration(
    workspace: Path,
    config: dict,
    iteration_num: int,
    state: OrchestratorState,
    dry_run: bool,
    program: str | None = None,
    workers: list[str] | None = None,
    chunk_info: dict | None = None,
) -> IterationResult:
    """Execute a single iteration via the Claude Agent SDK."""

    active_workers = workers or list(ALL_WORKERS)
    include_requirements = not workers or "requirements" in workers
    include_test_specs = not workers or "test-specs" in workers
    include_impl_plan = not workers or "implementation-plan" in workers

    step = len(active_workers) + 2

    if include_requirements:
        req_instruction = (
            f"{step}. After workers complete, spawn "
            f'the "requirements-deriver" subagent to synthesize capabilities and '
            f"modernization notes from the written artifacts."
        )
        step += 1
    else:
        req_instruction = ""

    if include_test_specs:
        if include_requirements:
            ts_instruction = (
                f"{step}. After the requirements-deriver completes, spawn "
                f'the "test-specs-deriver" subagent to derive stack-agnostic test '
                f"specifications from the business rules and requirements artifacts."
            )
        else:
            ts_instruction = (
                f"{step}. After workers complete, spawn "
                f'the "test-specs-deriver" subagent to derive stack-agnostic test '
                f"specifications from the business rules and requirements artifacts."
            )
        step += 1
    else:
        ts_instruction = ""

    if include_impl_plan:
        prev_agent = (
            '"test-specs-deriver"' if include_test_specs
            else '"requirements-deriver"' if include_requirements
            else "workers"
        )
        impl_instruction = (
            f"{step}. After {prev_agent} completes, spawn "
            f'the "implementation-plan-deriver" subagent to evaluate migration '
            f"strategies and create a phased migration plan from the capabilities "
            f"and dependency analysis."
        )
        step += 1
    else:
        impl_instruction = ""

    result_step = str(step)

    prompt = ORCHESTRATOR_PROMPT.format(
        iteration=iteration_num,
        application_name=config.get("application", "Unknown"),
        source_context=source_context(config),
        program_instruction=build_program_instruction(program),
        worker_list=build_worker_list_prompt(active_workers, WORKER_AGENT_MAP),
        requirements_instruction=req_instruction,
        test_specs_instruction=ts_instruction,
        impl_plan_instruction=impl_instruction,
        result_step=result_step,
        dry_run_instruction=build_dry_run_instruction(dry_run),
        previous_context=build_previous_context(state),
    )

    model = config.get("settings", {}).get("model")

    options = ClaudeAgentOptions(
        cwd=str(workspace),
        model=model,
        max_buffer_size=10 * 1024 * 1024,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "You are a COBOL reverse-engineering agent. Follow the "
                "CLAUDE.md output conventions when writing artifacts."
                + (f" This run is scoped to program {program} only." if program else "")
            ),
        },
        setting_sources=["project"],
        allowed_tools=["Read", "Write", "Glob", "Grep", "Skill", "Task"],
        permission_mode="acceptEdits",
        agents=_build_agents(config, program, workers, chunk_info=chunk_info,
                              workspace=workspace),
    )

    iter_label = f"iteration-{iteration_num}"
    if program:
        iter_label = f"{program}:{iter_label}"
    if chunk_info:
        iter_label = f"{program}:{chunk_info.get('chunk_id', '?')}:iter-{iteration_num}"

    result_text = ""
    sdk_error = False
    session_id = ""
    async for message in query(prompt=prompt, options=options):
        msg_type = getattr(message, "type", None)
        if isinstance(message, dict):
            msg_type = message.get("type", msg_type)

        if msg_type == "error":
            error_detail = (
                getattr(message, "error", None)
                or (message.get("error") if isinstance(message, dict) else None)
                or "unknown"
            )
            logger.error("SDK stream error: %s", error_detail)
            log_event("sdk_error", iteration=iter_label, error=str(error_detail))
            sdk_error = True
            continue

        msg_subtype = getattr(message, "subtype", "")

        if msg_subtype == "init":
            sid = getattr(message, "session_id", "")
            if sid:
                session_id = sid
            logger.info("Agent session started: %s", session_id)
            log_event("session_init", iteration=iter_label,
                       session_id=session_id)
        elif msg_subtype == "task_started":
            task_desc = (
                getattr(message, "description", "")
                or getattr(message, "agent_name", "")
                or getattr(message, "task_description", "")
                or ""
            )
            if not task_desc:
                tool_input = getattr(message, "tool_input", None)
                if isinstance(tool_input, dict):
                    task_desc = tool_input.get("description", "")
            logger.info(
                "Subagent started: %s",
                task_desc or "(unnamed)",
            )
            log_event("subagent_started", iteration=iter_label,
                       description=task_desc,
                       agent_id=getattr(message, "agent_id", ""))
        elif msg_subtype == "task_completed":
            agent_id = getattr(message, "agent_id", "")
            logger.info("Subagent completed: %s", agent_id)
            log_event("subagent_completed", iteration=iter_label,
                       agent_id=agent_id)
        elif msg_subtype == "success":
            logger.info("Agent completed successfully")
            sid = getattr(message, "session_id", "")
            if sid:
                session_id = sid
            log_event("session_success", iteration=iter_label,
                       session_id=session_id)

        for attr in ("result", "text", "content"):
            val = getattr(message, attr, None)
            if val and isinstance(val, str) and len(val) > 10:
                result_text = val
                logger.debug(
                    "Captured text (%d chars): %s...", len(val), val[:150]
                )
                break

        msg_obj = getattr(message, "message", None)
        if msg_obj:
            content_blocks = getattr(msg_obj, "content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    block_type = getattr(block, "type", "")
                    if block_type == "text":
                        text = getattr(block, "text", "")
                        if text and len(text) > 10:
                            result_text = text
                            logger.debug(
                                "Captured block text (%d chars)", len(text)
                            )
                    elif block_type == "tool_use":
                        tool_name = getattr(block, "name", "")
                        tool_input = getattr(block, "input", {})
                        if tool_name == "Write" and isinstance(tool_input, dict):
                            file_path = tool_input.get("file_path", "")
                            logger.info("Agent writing: %s", file_path)
                            log_event("tool_use", iteration=iter_label,
                                       tool="Write", file_path=file_path)
                        elif tool_name == "Task" and isinstance(tool_input, dict):
                            desc = tool_input.get("description", "")
                            logger.info("Agent spawning task: %s", desc)
                            log_event("tool_use", iteration=iter_label,
                                       tool="Task", description=desc)
                        else:
                            logger.debug("Agent calling tool: %s", tool_name)
                            log_event("tool_use", iteration=iter_label,
                                       tool=tool_name)

    if session_id:
        capture_session_transcript(session_id, iter_label)

    if sdk_error and not result_text:
        logger.warning(
            "Iteration %d had SDK errors and no result — returning empty result",
            iteration_num,
        )
        log_event("iteration_empty", iteration=iter_label, reason="sdk_errors")
        return IterationResult(iteration=iteration_num)

    logger.info("Final result_text length: %d", len(result_text))
    if result_text:
        logger.debug("Final result preview: %s", result_text[:300])
    return _parse_iteration_result(result_text, iteration_num)


def _log_critic_tool_use(message: object) -> None:
    """Extract and log any tool_use from a critic SDK message."""
    msg_obj = getattr(message, "message", None)
    if msg_obj:
        for block in getattr(msg_obj, "content", []) or []:
            if getattr(block, "type", "") == "tool_use":
                tool_name = getattr(block, "name", "")
                tool_input = getattr(block, "input", {}) or {}
                _emit_critic_tool_log(tool_name, tool_input)
                return

    tool_name = getattr(message, "tool_name", "") or getattr(message, "name", "")
    if tool_name:
        tool_input = getattr(message, "tool_input", {}) or getattr(message, "input", {}) or {}
        _emit_critic_tool_log(tool_name, tool_input)
        return

    if getattr(message, "subtype", "") == "tool_use":
        tool_name = getattr(message, "tool", "") or ""
        tool_input = getattr(message, "input", {}) or {}
        _emit_critic_tool_log(tool_name, tool_input)


def _emit_critic_tool_log(tool_name: str, tool_input: dict) -> None:
    """Format and emit a log line for a critic tool call."""
    if not tool_name:
        return
    if tool_name == "Write":
        path = tool_input.get("file_path", "") or tool_input.get("path", "")
        logger.info("Critic fixing: %s", path)
    elif tool_name in ("Read", "Grep", "Glob"):
        target = (
            tool_input.get("file_path", "")
            or tool_input.get("path", "")
            or tool_input.get("pattern", "")
            or tool_input.get("glob_pattern", "")
            or ""
        )
        logger.debug("Critic %s: %s", tool_name, target)


async def run_critic_pass(
    workspace: Path,
    config: dict,
    *,
    phase: str,
    program: str | None = None,
) -> None:
    """Run the LLM critic as a corrective pass after deterministic validation.

    The critic reads written artifacts, cross-checks them against source code,
    and fixes issues in place.  Runs once after Phase 1 (cross-cutting review)
    and optionally after Phase 2 (per-program review).
    """
    from prompts.critic import build_critic_prompt

    prompt = build_critic_prompt(config, phase=phase, program=program)
    model = config.get("settings", {}).get("model")

    print(f"\n  --- Critic review ({phase}) ---")

    options = ClaudeAgentOptions(
        cwd=str(workspace),
        model=model,
        max_buffer_size=10 * 1024 * 1024,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "You are a senior COBOL architect reviewing analysis artifacts. "
                "Fix any issues you find directly in the output files."
            ),
        },
        setting_sources=["project"],
        allowed_tools=["Read", "Write", "Glob", "Grep"],
        permission_mode="acceptEdits",
    )

    critic_session_id = ""
    with trace_span(f"critic:{phase}", attributes={"phase": phase}):
        async for message in query(prompt=prompt, options=options):
            msg_subtype = getattr(message, "subtype", "")
            if msg_subtype == "init":
                sid = getattr(message, "session_id", "")
                if sid:
                    critic_session_id = sid
                logger.info("Critic session started")
                log_event("critic_init", phase=phase, session_id=critic_session_id)
            elif msg_subtype == "success":
                logger.info("Critic completed")
                log_event("critic_success", phase=phase,
                           session_id=critic_session_id)

            _log_critic_tool_use(message)

    if critic_session_id:
        capture_session_transcript(critic_session_id, f"critic-{phase}")
    print(f"  Critic review complete ({phase}).")
