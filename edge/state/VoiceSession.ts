import type {
  AudioSessionSnapshot,
  AudioSessionStatus,
  ProcessingBoundary,
} from "../ports/audio.js";

export type ProcessingOnlyValues = Readonly<Record<string, unknown>>;
export interface VoiceSessionOpenInput {
  readonly sessionId: string; readonly processingBoundary: ProcessingBoundary; readonly turnEpoch: number;
  readonly activeStreamId: string | null; readonly startedAtIso: string; readonly processingOnlyValues: Readonly<Record<string, unknown>>;
}
export interface VoiceSessionDegradeInput {
  readonly reason: string;
}
export interface VoiceSessionCloseInput {
  readonly reason: string; readonly endedAtIso: string;
}
const IDENTIFIER_PATTERN = /^[a-z0-9][a-z0-9._-]{2,127}$/;
function assertIdentifier(value: string, field: string): void {
  if (!IDENTIFIER_PATTERN.test(value)) {
    throw new Error(`${field} must match the deterministic session ID pattern`);
  }
}
function assertNonEmpty(value: string, field: string): void {
  if (value.length === 0) {
    throw new Error(`${field} must not be empty`);
  }
}
function assertEpoch(value: number, field: string): void {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error(`${field} must be a non-negative safe integer`);
  }
}
function assertBoundary(value: ProcessingBoundary, field: string): void {
  if (value !== "localOnly" && value !== "consentedCloud") {
    throw new Error(`${field} must be localOnly or consentedCloud`);
  }
}
/** One immutable, in-memory voice session state object. */
export class VoiceSession {
  readonly #sessionId: string;
  readonly #status: AudioSessionStatus;
  readonly #processingBoundary: ProcessingBoundary;
  readonly #turnEpoch: number;
  readonly #activeStreamId: string | null;
  readonly #startedAtIso: string;
  readonly #endedAtIso: string | null;
  readonly #processingOnlyValues: ProcessingOnlyValues;

  private constructor(input: {
    sessionId: string; status: AudioSessionStatus; processingBoundary: ProcessingBoundary; turnEpoch: number;
    activeStreamId: string | null; startedAtIso: string; endedAtIso: string | null; processingOnlyValues: ProcessingOnlyValues;
  }) {
    this.#sessionId = input.sessionId;
    this.#status = input.status;
    this.#processingBoundary = input.processingBoundary;
    this.#turnEpoch = input.turnEpoch;
    this.#activeStreamId = input.activeStreamId;
    this.#startedAtIso = input.startedAtIso;
    this.#endedAtIso = input.endedAtIso;
    this.#processingOnlyValues = input.processingOnlyValues;
  }

  static open(input: VoiceSessionOpenInput): VoiceSession {
    assertIdentifier(input.sessionId, "sessionId");
    assertEpoch(input.turnEpoch, "turnEpoch");
    assertNonEmpty(input.startedAtIso, "startedAtIso");
    if (input.activeStreamId !== null) {
      assertIdentifier(input.activeStreamId, "activeStreamId");
    }
    assertBoundary(input.processingBoundary, "processingBoundary");

    return new VoiceSession({
      ...input,
      status: "active",
      endedAtIso: null,
      processingOnlyValues: Object.freeze({ ...input.processingOnlyValues }),
    });
  }

  get snapshot(): AudioSessionSnapshot {
    return Object.freeze({
      sessionId: this.#sessionId,
      status: this.#status,
      processingBoundary: this.#processingBoundary,
      turnEpoch: this.#turnEpoch,
      activeStreamId: this.#activeStreamId,
      startedAtIso: this.#startedAtIso,
      endedAtIso: this.#endedAtIso,
    });
  }

  get processingOnlyValues(): ProcessingOnlyValues {
    return this.#processingOnlyValues;
  }

  start(): VoiceSession {
    if (this.#status !== "active") {
      throw new Error("only an active session can ignore duplicate start");
    }
    return this;
  }

  degrade(_input: VoiceSessionDegradeInput): VoiceSession {
    if (this.#status !== "active") {
      throw new Error("only an active session can degrade");
    }
    return new VoiceSession({
      sessionId: this.#sessionId,
      status: "degraded",
      processingBoundary: this.#processingBoundary,
      turnEpoch: this.#turnEpoch,
      activeStreamId: this.#activeStreamId,
      startedAtIso: this.#startedAtIso,
      endedAtIso: null,
      processingOnlyValues: this.#processingOnlyValues,
    });
  }

  close(input: VoiceSessionCloseInput): VoiceSession {
    if (this.#status === "closed") {
      throw new Error("a closed session is final");
    }
    assertNonEmpty(input.reason, "reason");
    assertNonEmpty(input.endedAtIso, "endedAtIso");
    return new VoiceSession({
      sessionId: this.#sessionId,
      status: "closed",
      processingBoundary: this.#processingBoundary,
      turnEpoch: this.#turnEpoch,
      activeStreamId: this.#activeStreamId,
      startedAtIso: this.#startedAtIso,
      endedAtIso: input.endedAtIso,
      processingOnlyValues: Object.freeze({}),
    });
  }
}
