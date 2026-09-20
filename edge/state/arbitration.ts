export type PresentationChannel = "text" | "speech" | "textAndSpeech";
export type PresentationSource = "response" | "slowPath" | "activeUser";
export type PresentationTerminalState = "rendered" | "canceled";
export type ArbitrationAction = "present" | "reject" | "supersede";

export interface AccessibilityMetadata {
  readonly screenReaderText: string;
  readonly captionsAvailable: boolean;
}

export interface ResponseCandidate {
  readonly responseId: string;
  readonly turnId: string;
  readonly typedText: string;
  readonly spokenText: string;
  readonly semanticParityHash: string;
  readonly channel: PresentationChannel;
  readonly priority: number;
  readonly turnEpoch: number;
  readonly source: PresentationSource;
  readonly terminalState: PresentationTerminalState;
  readonly accessibility: AccessibilityMetadata;
}

export interface ArbitrationDecision {
  readonly action: ArbitrationAction;
  readonly activeStreamId: string | null;
  readonly rejectionReason: null | string;
  readonly supersededStreamId: string | null;
}

export interface PresentationArbiterSnapshot {
  readonly sessionId: string;
  readonly currentTurnEpoch: number;
  readonly activeStreamId: string | null;
}

export interface PresentationArbiterOpenInput {
  readonly sessionId: string;
  readonly currentTurnEpoch: number;
  readonly activeStreamId: string | null;
}

const CANDIDATE_FIELDS = new Set([
  "responseId", "turnId", "typedText", "spokenText", "semanticParityHash", "channel",
  "priority", "turnEpoch", "source", "terminalState", "accessibility",
]);
const ACCESSIBILITY_FIELDS = new Set(["screenReaderText", "captionsAvailable"]);
const IDENTIFIER_PATTERN = /^[a-z0-9][a-z0-9._-]{2,127}$/;
const HASH_PATTERN = /^[0-9a-f]{64}$/;
const MAX_PRESENTATION_LENGTH = 240;

function isIdentifier(value: string): boolean {
  return IDENTIFIER_PATTERN.test(value);
}

function isSafeEpoch(value: number): boolean {
  return Number.isSafeInteger(value) && value >= 0;
}

function hasExactFields(value: object, allowed: Set<string>): boolean {
  const fields = Object.keys(value);
  return fields.length === allowed.size && fields.every((field) => allowed.has(field));
}

function codePointLength(value: string): number {
  let length = 0;
  for (let index = 0; index < value.length; index += 1) {
    if (value.charCodeAt(index) >= 0xd800 && value.charCodeAt(index) <= 0xdbff) index += 1;
    length += 1;
  }
  return length;
}

function semanticKey(value: string): string {
  return Array.from(value.normalize("NFKC").toLowerCase())
    .filter((character) => /[\p{L}\p{N}]/u.test(character))
    .join("");
}

function hasEmptyPresentation(candidate: ResponseCandidate): boolean {
  return codePointLength(candidate.typedText) === 0
    || codePointLength(candidate.spokenText) === 0;
}

function hasOverlongPresentation(candidate: ResponseCandidate): boolean {
  return codePointLength(candidate.typedText) > MAX_PRESENTATION_LENGTH
    || codePointLength(candidate.spokenText) > MAX_PRESENTATION_LENGTH;
}

function hasAccessiblePresentation(candidate: ResponseCandidate): boolean {
  const accessibility = candidate.accessibility;
  return typeof accessibility.screenReaderText === "string"
    && codePointLength(accessibility.screenReaderText) > 0
    && codePointLength(accessibility.screenReaderText) <= MAX_PRESENTATION_LENGTH
    && accessibility.captionsAvailable === true
    && (candidate.channel !== "speech" || accessibility.captionsAvailable);
}

function decision(
  action: ArbitrationAction,
  activeStreamId: string | null,
  rejectionReason: null | string = null,
  supersededStreamId: string | null = null,
): ArbitrationDecision {
  return Object.freeze({
    action,
    activeStreamId,
    rejectionReason,
    supersededStreamId,
  });
}

function reject(activeStreamId: string | null, reason: string): ArbitrationDecision {
  return decision("reject", activeStreamId, reason);
}

function structuralRejection(candidate: ResponseCandidate, currentTurnEpoch: number): string | null {
  const accessibility = candidate.accessibility as AccessibilityMetadata | undefined;
  if (!hasExactFields(candidate, CANDIDATE_FIELDS)
    || accessibility === undefined || !hasExactFields(accessibility, ACCESSIBILITY_FIELDS)) {
    return "processing-value-rejected";
  }
  if (!isIdentifier(candidate.responseId) || !isIdentifier(candidate.turnId)
    || !Number.isSafeInteger(candidate.priority) || candidate.priority < 0
    || !["text", "speech", "textAndSpeech"].includes(candidate.channel)
    || !["response", "slowPath", "activeUser"].includes(candidate.source)
    || !["rendered", "canceled"].includes(candidate.terminalState)) {
    return "invalid-candidate";
  }
  if (candidate.turnEpoch !== currentTurnEpoch) return "stale-turn-epoch";
  if (candidate.terminalState === "canceled") return "canceled-response";
  return null;
}

function presentationRejection(candidate: ResponseCandidate): string | null {
  if (hasOverlongPresentation(candidate)) return "presentation-too-long";
  if (hasEmptyPresentation(candidate)
    || semanticKey(candidate.typedText) !== semanticKey(candidate.spokenText)
    || !HASH_PATTERN.test(candidate.semanticParityHash)) {
    return "parity-mismatch";
  }
  if (!hasAccessiblePresentation(candidate)) return "inaccessible-presentation";
  return null;
}

/** Arbitrates one accessible presentation stream without retaining presentation payloads. */
export class PresentationArbiter {
  readonly #sessionId: string;
  readonly #currentTurnEpoch: number;
  #activeStreamId: string | null;
  #activePriority: number | null;

  private constructor(input: PresentationArbiterOpenInput) {
    this.#sessionId = input.sessionId;
    this.#currentTurnEpoch = input.currentTurnEpoch;
    this.#activeStreamId = input.activeStreamId;
    this.#activePriority = input.activeStreamId === null ? null : 0;
  }

  static open(input: PresentationArbiterOpenInput): PresentationArbiter {
    if (!isIdentifier(input.sessionId) || !isSafeEpoch(input.currentTurnEpoch)
      || (input.activeStreamId !== null && !isIdentifier(input.activeStreamId))) {
      throw new Error("presentation arbiter identity is invalid");
    }
    return new PresentationArbiter(input);
  }

  get snapshot(): PresentationArbiterSnapshot {
    return Object.freeze({
      sessionId: this.#sessionId,
      currentTurnEpoch: this.#currentTurnEpoch,
      activeStreamId: this.#activeStreamId,
    });
  }

  submit(candidate: ResponseCandidate): ArbitrationDecision {
    const rejection = structuralRejection(candidate, this.#currentTurnEpoch)
      ?? presentationRejection(candidate);
    if (rejection !== null) return reject(this.#activeStreamId, rejection);
    if (this.#activeStreamId !== null && this.#activePriority !== null
      && candidate.priority <= this.#activePriority) {
      return reject(this.#activeStreamId, "stream-active");
    }

    const superseded = this.#activeStreamId;
    this.#activeStreamId = candidate.responseId;
    this.#activePriority = candidate.priority;
    return superseded === null
      ? decision("present", candidate.responseId)
      : decision("supersede", candidate.responseId, null, superseded);
  }
}
