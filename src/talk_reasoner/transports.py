from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from talk_reasoner.actions import ActionCatalog, ActionProposal
from talk_reasoner.contracts import CREDENTIAL_PATTERNS
REASONER_SCHEMA_VERSION = "slice0-reasoner-proposal-v1"
REQUEST_SCHEMA_VERSION = "slice0-job-request-v1"
PROVENANCE_SCHEMA_VERSION = "slice0-reasoner-provenance-v1"
class TransportContractError(ValueError):
    """A scripted offline proposal violates the reasoner boundary."""
class MonotonicClock(Protocol):
    def now(self) -> float: ...
    async def wait(self, seconds: float) -> None: ...
@dataclass(frozen=True, slots=True)
class NoAction: reason: str
@dataclass(frozen=True, slots=True)
class ReasonerProvenance: schema_version: str; fixture_set_version: str; source: str; model_id: str; review_status: str
@dataclass(frozen=True, slots=True)
class ReasonerRequest: schema_version: str; job_id: str; session_id: str; turn_id: str; turn_epoch: int; input_hash: str; catalog_hash: str; policy_version: str
@dataclass(frozen=True, slots=True)
class ReasonerProposal:
    schema_version: str; job_id: str; session_id: str; turn_id: str; turn_epoch: int; candidate_answer: str
    actions: tuple[ActionProposal, ...]; no_action: NoAction | None; state_updates: Mapping[str, str]; confidence: float
    uncertainty: float; input_hash: str; catalog_hash: str; policy_version: str
    provenance: ReasonerProvenance; refusal_reason: str | None = None
class ReasonerTransport(Protocol):
    async def propose(self, request: ReasonerRequest) -> ReasonerProposal: ...
def _forbidden(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(isinstance(key, str) and _forbidden(key) or _forbidden(child) for key, child in value.items())
    return isinstance(value, str) and any(pattern.search(value) for pattern in CREDENTIAL_PATTERNS)


def validate_proposal(proposal: ReasonerProposal, request: ReasonerRequest, catalog: ActionCatalog) -> None:
    """Validate one typed local proposal without executing or trusting it."""
    identity = (proposal.schema_version, proposal.job_id, proposal.session_id, proposal.turn_id, proposal.turn_epoch)
    expected = (REASONER_SCHEMA_VERSION, request.job_id, request.session_id, request.turn_id, request.turn_epoch)
    if identity != expected or proposal.input_hash != request.input_hash or proposal.catalog_hash != request.catalog_hash: raise TransportContractError("proposal identity or hash does not match the scoped request")
    if proposal.policy_version != request.policy_version or proposal.policy_version != catalog.policy.policy_version: raise TransportContractError("proposal policy version is not evaluable")
    if not 0 <= proposal.confidence <= 1 or not 0 <= proposal.uncertainty <= 1 or proposal.confidence + proposal.uncertainty > 1: raise TransportContractError("confidence and uncertainty must be bounded")
    if not 1 <= len(proposal.candidate_answer) <= 512 or _forbidden(proposal): raise TransportContractError("candidate answer is unbounded or unsafe")
    if bool(proposal.actions) == (proposal.no_action is not None) or proposal.refusal_reason is not None and proposal.actions: raise TransportContractError("proposal must contain exactly one action marker")
    if proposal.refusal_reason is not None and not 8 <= len(proposal.refusal_reason) <= 256: raise TransportContractError("refusal reason must be bounded")
    if not 0 <= len(proposal.state_updates) <= 4 or any(not 1 <= len(key) <= 64 or not 8 <= len(value) <= 256 for key, value in proposal.state_updates.items()): raise TransportContractError("state updates must be bounded and justified")
    provenance = proposal.provenance
    if (provenance.schema_version, provenance.source, provenance.review_status) != (PROVENANCE_SCHEMA_VERSION, "local-scripted-transport", "reviewed"): raise TransportContractError("proposal provenance is not the reviewed local transport")
    if not provenance.fixture_set_version or not provenance.model_id: raise TransportContractError("proposal provenance is incomplete")
    for item in proposal.actions:
        fields = (item.job_id, item.session_id, item.turn_id, item.turn_epoch, item.catalog_version, item.policy_version)
        request_fields = (request.job_id, request.session_id, request.turn_id, request.turn_epoch, catalog.catalog_version, catalog.policy.policy_version)
        if fields != request_fields or not isinstance(item.arguments, Mapping): raise TransportContractError("action proposal identity or typing is invalid")


@dataclass(frozen=True, slots=True)
class LocalScriptedTransport:
    """Deterministic, offline Slice-0 source of exactly one typed proposal."""

    proposals: ReasonerProposal | tuple[ReasonerProposal, ...]; delay_seconds: float; clock: MonotonicClock; call_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.proposals, tuple): object.__setattr__(self, "proposals", (self.proposals,))
        if not self.proposals or not all(isinstance(item, ReasonerProposal) for item in self.proposals): raise TransportContractError("at least one typed scripted proposal is required")
        if not math.isfinite(self.delay_seconds) or self.delay_seconds < 0: raise TransportContractError("logical delay must be finite and non-negative")

    async def propose(self, request: ReasonerRequest) -> ReasonerProposal:
        """Return one prevalidated proposal after an injectable logical delay."""
        if request.schema_version != REQUEST_SCHEMA_VERSION: raise TransportContractError("unsupported transport request schema")
        object.__setattr__(self, "call_count", self.call_count + 1)
        if self.call_count > len(self.proposals): raise TransportContractError("scripted transport exhausted")
        await self.clock.wait(self.delay_seconds)
        return self.proposals[self.call_count - 1]
