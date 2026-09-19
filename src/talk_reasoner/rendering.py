from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from types import MappingProxyType
from typing import Literal, NamedTuple

from talk_reasoner.actions import ValidatedAction
from talk_reasoner.contracts import CREDENTIAL_PATTERNS, ID_PATTERN
from talk_reasoner.jobs import TerminalOutcome

RENDER_SCHEMA_VERSION = "slice0-rendered-response-v1"
RenderState = Literal["chitchat", "unclear", "pending", "running", "waiting_confirmation", "completed", "canceled", "downgraded", "failed"]
RENDER_STATES = frozenset(("chitchat", "unclear", "waiting_confirmation", "completed", "canceled", "downgraded", "failed"))
FORBIDDEN_CONTENT = (re.compile(r"(?i)\b(schema|schemas|schema_version|stack trace|traceback|tool log|tool output|hidden prompt|system prompt|private context|private tool output|unreviewed tool output|event body|event_type|chain_hash|prior_event_hash|candidate_answer|model output|raw output|debug dump)\b"),
                     re.compile(r"(?s)(?:^\s*[{[]|\"[^\"\n]{1,64}\"\s*:|[a-z_][a-z0-9_]*\s*=\s*[\"{[])"),) + CREDENTIAL_PATTERNS

class RenderError(ValueError):
    """A terminal outcome cannot be presented without leaking internal data."""

class PresentationConstraints(NamedTuple):
    response_id: str; channel: str = "text"; screen_reader: bool = True; max_text_length: int = 240
    validated_action: ValidatedAction | None = None; validated_answer: str | None = None

class RenderedResponse(NamedTuple):
    response_id: str; text: str; channel: str; priority: int; turn_epoch: int; latency_ms: int
    provenance: MappingProxyType[str, str]

def _clean(value: str, label: str, constraints: PresentationConstraints) -> str:
    text = value.strip()
    if not text or not constraints.screen_reader and "\n" in text:
        raise RenderError(f"{label} must be non-empty, single-response text")
    if len(text) > constraints.max_text_length or any(pattern.search(text) for pattern in FORBIDDEN_CONTENT):
        raise RenderError(f"{label} is forbidden, internal, or too long")
    return text

def _provenance(value: object) -> MappingProxyType[str, str]:
    if hasattr(value, "_asdict"): source = getattr(value, "_asdict")()
    elif is_dataclass(value) and not isinstance(value, type): source = asdict(value)
    else: raise RenderError("provenance must be typed")
    fields = ("schema_version", "fixture_set_version", "source", "model_id", "review_status")
    provenance = {field: source[field] for field in fields if field in source}
    if "source" not in provenance or not all(isinstance(item, str) and item for item in provenance.values()):
        raise RenderError("provenance is incomplete")
    return MappingProxyType(provenance)

def _arguments(action: ValidatedAction) -> str:
    values = action.canonical_arguments
    terms = values.get("terms", ()); detail = f", matching “{', '.join(terms)}”" if terms else ", with no filter terms"
    if action.action_name == "search": return f"for “{values['query']}” with at most {values.get('limit', 10)} results{detail}"
    if action.action_name == "read_state": return f"the “{values['key']}” value{detail}"
    return f"“{values['value']}” to “{values['key']}”{detail}"

def _verb(action: ValidatedAction) -> str:
    return {"write_state": "Save", "search": "Search", "read_state": "Read"}[action.action_name]

def _target(target: str) -> str:
    if target != "fixture://slice0": raise RenderError("confirmation target is outside the local fixture boundary")
    return "your local fixture state"

def render_response(outcome: TerminalOutcome, *, constraints: PresentationConstraints) -> RenderedResponse:
    """Render exactly one clean, speech-first response from one terminal outcome."""
    if outcome.state not in RENDER_STATES or outcome.terminal_reason is None:
        raise RenderError("outcome state is ambiguous or not renderable")
    if not ID_PATTERN.fullmatch(constraints.response_id) or constraints.channel != "text":
        raise RenderError("response identity or channel is invalid")
    if outcome.state == "completed" and not outcome.normal_result_allowed:
        raise RenderError("completed outcome does not allow a normal result")
    if outcome.state in {"unclear", "waiting_confirmation", "canceled", "downgraded", "failed"} and outcome.normal_result_allowed:
        raise RenderError("only a completed outcome may be rendered as a normal result")
    if outcome.state == "waiting_confirmation":
        if constraints.validated_action is None: raise RenderError("confirmation requires a validated action")
        action = constraints.validated_action; arguments = _arguments(action)
        text = (f"{_verb(action)} {arguments} in {_target(action.target)}, one time now? "
                f"It is reversible here, and no tool will run until you say yes. Reply yes to confirm, or no to cancel.")
    else:
        copies = {"chitchat": "Hi — I'm here.", "unclear": "Could you clarify exactly what you'd like me to check or change?",
                  "canceled": "", "failed": "That request couldn't be completed safely. Please rephrase it and try again.",
                  "downgraded": "That work was set aside. You can ask to resume it later."}
        text = constraints.validated_answer if outcome.state == "completed" and constraints.validated_answer is not None else outcome.safe_summary if outcome.state == "completed" else copies[outcome.state]
    rendered = "" if outcome.state == "canceled" else _clean(text, f"{outcome.state} response", constraints)
    return RenderedResponse(constraints.response_id, rendered, constraints.channel, outcome.response_priority,
                            outcome.turn_epoch, outcome.latency_ms, _provenance(outcome.provenance))
