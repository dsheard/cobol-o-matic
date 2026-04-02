"""Prompt builders for COBOL reverse-engineering agents."""

from .inventory import build_inventory_worker_prompt
from .data import build_data_worker_prompt
from .business_rules import build_business_rules_worker_prompt
from .flow import build_flow_worker_prompt
from .integration import build_integration_worker_prompt
from .requirements import build_requirements_prompt
from .test_specs import build_test_specs_prompt
from .implementation import build_implementation_plan_prompt
from .orchestrator import (
    ORCHESTRATOR_PROMPT,
    build_worker_list_prompt,
    build_dry_run_instruction,
    build_program_instruction,
    build_previous_context,
)
from ._helpers import source_context

__all__ = [
    "build_inventory_worker_prompt",
    "build_data_worker_prompt",
    "build_business_rules_worker_prompt",
    "build_flow_worker_prompt",
    "build_integration_worker_prompt",
    "build_requirements_prompt",
    "build_test_specs_prompt",
    "build_implementation_plan_prompt",
    "ORCHESTRATOR_PROMPT",
    "build_worker_list_prompt",
    "build_dry_run_instruction",
    "build_program_instruction",
    "build_previous_context",
    "source_context",
]
