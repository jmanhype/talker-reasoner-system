import type { ProcessingBoundary } from "../ports/audio.js";

export type ConversationTurnStatus = "Receiving" | "Routed" | "Responding" | "Terminal";
export type RouteName = "chitchat" | "needs_tools" | "unclear";
export type RoutingRisk = "low" | "medium" | "high" | "unevaluable";
export interface ConversationTurnOpenInput {
  readonly sessionId: string; readonly turnId: string; readonly turnEpoch: number;
  readonly processingBoundary: ProcessingBoundary;
}
export interface TranscribeInput {
  readonly transcript: string; readonly processingBoundary: ProcessingBoundary;
  readonly cloudConsent: boolean; readonly schemaVersion: string;
}

export interface RouteDecision {
  readonly selectedLabel: string; readonly route: RouteName; readonly confidence: number; readonly risk: RoutingRisk;
  readonly thresholdsVersion: string; readonly policyHash: string; readonly inputHash: string;
  readonly fallbackReason: null | "threshold" | "safety" | "invalid";
}

export interface RenderedResponse {
  readonly responseId: string; readonly text: string; readonly channel: string; readonly priority: number;
  readonly turnEpoch: number; readonly latencyMs: number;
  readonly provenance: Readonly<Record<string, string>>;
}

export interface ConversationTurnSnapshot {
  readonly sessionId: string; readonly turnId: string; readonly turnEpoch: number; readonly status: ConversationTurnStatus;
  readonly processingBoundary: ProcessingBoundary; readonly inputHash: string | null; readonly ephemeralTranscript: string | null;
  readonly boundRoute: RouteDecision | null;
  readonly boundResponse: RenderedResponse | null;
}

const IDENTIFIER_PATTERN = /^[a-z0-9][a-z0-9._-]{2,127}$/;
const VERSION_PATTERN = /^[a-z0-9][a-z0-9._-]{0,63}$/;
const HASH_PATTERN = /^[0-9a-f]{64}$/;
const CREDENTIAL_PATTERNS = [
  /(?:api[_-]?key|password|passwd|secret|bearer\s+|access[_-]?token|authorization)/i,
  /AKIA[0-9A-Z]{16}/,
  /sk-[A-Za-z0-9_-]{16,}/,
];

function assertIdentifier(value: string, field: string): void {
  if (!IDENTIFIER_PATTERN.test(value)) {
    throw new Error(`${field} must match the deterministic ID pattern`);
  }
}

function assertVersion(value: string, field: string): void {
  if (!VERSION_PATTERN.test(value)) {
    throw new Error(`${field} must match the deterministic version pattern`);
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

function validatedTranscriptLength(value: string): number {
  let length = 0;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code >= 0xd800 && code <= 0xdbff) {
      const low = value.charCodeAt(index + 1);
      if (low < 0xdc00 || low > 0xdfff) {
        throw new Error("transcript must contain valid Unicode");
      }
      index += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) {
      throw new Error("transcript must contain valid Unicode");
    }
    length += 1;
  }
  return length;
}

function jsonString(value: string): string {
  let result = '"';
  for (const character of value) {
    const code = character.codePointAt(0);
    if (code === undefined) {
      throw new Error("a canonical hash input contained invalid Unicode");
    }
    if (character === '"') result += '\\"';
    else if (character === "\\") result += "\\\\";
    else if (code === 0x08) result += "\\b";
    else if (code === 0x09) result += "\\t";
    else if (code === 0x0a) result += "\\n";
    else if (code === 0x0c) result += "\\f";
    else if (code === 0x0d) result += "\\r";
    else if (code < 0x20) {
      result += `\\u00${code.toString(16).padStart(2, "0")}`;
    } else result += character;
  }
  return `${result}"`;
}

function rotr(value: number, bits: number): number {
  return (value >>> bits) | (value << (32 - bits));
}

function sha256Hex(value: string): string {
  const bytes = Array.from(new TextEncoder().encode(value));
  const bitLength = BigInt(bytes.length * 8);
  const padded = [...bytes, 0x80];
  while (padded.length % 64 !== 56) padded.push(0);
  for (let shift = 56n; shift >= 0n; shift -= 8n) {
    padded.push(Number((bitLength >> shift) & 0xffn));
  }

  const hashes = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
  ];
  const roundConstants = ("428a2f98 71374491 b5c0fbcf e9b5dba5 3956c25b 59f111f1 923f82a4 ab1c5ed5 "
    + "d807aa98 12835b01 243185be 550c7dc3 72be5d74 80deb1fe 9bdc06a7 c19bf174 "
    + "e49b69c1 efbe4786 0fc19dc6 240ca1cc 2de92c6f 4a7484aa 5cb0a9dc 76f988da "
    + "983e5152 a831c66d b00327c8 bf597fc7 c6e00bf3 d5a79147 06ca6351 14292967 "
    + "27b70a85 2e1b2138 4d2c6dfc 53380d13 650a7354 766a0abb 81c2c92e 92722c85 "
    + "a2bfe8a1 a81a664b c24b8b70 c76c51a3 d192e819 d6990624 f40e3585 106aa070 "
    + "19a4c116 1e376c08 2748774c 34b0bcb5 391c0cb3 4ed8aa4a 5b9cca4f 682e6ff3 "
    + "748f82ee 78a5636f 84c87814 8cc70208 90befffa a4506ceb bef9a3f7 c67178f2"
  ).split(" ").map((word) => Number.parseInt(word, 16));

  for (let offset = 0; offset < padded.length; offset += 64) {
    const words = new Array<number>(64).fill(0);
    for (let index = 0; index < 16; index += 1) {
      const position = offset + index * 4;
      words[index] = ((padded[position] << 24) | (padded[position + 1] << 16)
        | (padded[position + 2] << 8) | padded[position + 3]) >>> 0;
    }
    for (let index = 16; index < 64; index += 1) {
      const s0 = rotr(words[index - 15], 7) ^ rotr(words[index - 15], 18) ^ (words[index - 15] >>> 3);
      const s1 = rotr(words[index - 2], 17) ^ rotr(words[index - 2], 19) ^ (words[index - 2] >>> 10);
      words[index] = (words[index - 16] + s0 + words[index - 7] + s1) >>> 0;
    }

    let [a, b, c, d, e, f, g, h] = hashes;
    for (let index = 0; index < 64; index += 1) {
      const upper = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temporary = (h + upper + choice + roundConstants[index] + words[index]) >>> 0;
      const lower = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temporaryTwo = (temporary + lower + majority) >>> 0;
      h = g;
      g = f;
      f = e;
      e = (d + temporary) >>> 0;
      d = c;
      c = b;
      b = a;
      a = temporaryTwo;
    }
    const next = [a, b, c, d, e, f, g, h];
    for (let index = 0; index < 8; index += 1) {
      hashes[index] = (hashes[index] + next[index]) >>> 0;
    }
  }
  return hashes.map((word) => word.toString(16).padStart(8, "0")).join("");
}

function scopedInputHash(transcript: string, schemaVersion: string): string {
  const canonical = `{${jsonString("content")}:${jsonString(transcript)},`
    + `${jsonString("content_encoding")}:${jsonString("utf8")},`
    + `${jsonString("schema_version")}:${jsonString(schemaVersion)},`
    + `${jsonString("scope")}:${jsonString("fixture-input")}}`;
  return sha256Hex(canonical);
}

function boundaryIsConsented(
  sessionBoundary: ProcessingBoundary,
  input: TranscribeInput,
): boolean {
  if (sessionBoundary !== input.processingBoundary) return false;
  return input.processingBoundary === "consentedCloud" ? input.cloudConsent : !input.cloudConsent;
}

function normalizeRoute(decision: RouteDecision): RouteDecision {
  const allowed = new Set([
    "selectedLabel", "route", "confidence", "risk", "thresholdsVersion", "policyHash", "inputHash", "fallbackReason",
  ]);
  if (Object.keys(decision).some((key) => !allowed.has(key))) {
    throw new Error("routing decision contains unknown fields");
  }
  if (decision.route === "needs_tools") {
    throw new Error("M2 binds only a valid non-tool route");
  }
  if (decision.route !== "chitchat" && decision.route !== "unclear") {
    throw new Error("route must be chitchat, needs_tools, or unclear");
  }
  if (decision.selectedLabel.length === 0 || !Number.isFinite(decision.confidence)
    || decision.confidence < 0 || decision.confidence > 1) {
    throw new Error("routing label or confidence is invalid");
  }
  const risks = new Set(["low", "medium", "high", "unevaluable"]);
  if (!risks.has(decision.risk) || !HASH_PATTERN.test(decision.policyHash)
    || !HASH_PATTERN.test(decision.inputHash)) {
    throw new Error("routing risk or hash is invalid");
  }
  assertVersion(decision.thresholdsVersion, "thresholdsVersion");
  if (decision.fallbackReason !== null
    && !["threshold", "safety", "invalid"].includes(decision.fallbackReason)) {
    throw new Error("fallbackReason is invalid");
  }
  return Object.freeze({ ...decision });
}

function normalizeResponse(response: RenderedResponse): RenderedResponse {
  if (!IDENTIFIER_PATTERN.test(response.responseId) || response.text.length === 0
    || response.channel !== "text" || !Number.isSafeInteger(response.priority)
    || response.priority < 0 || !Number.isSafeInteger(response.turnEpoch)
    || response.turnEpoch < 0 || !Number.isSafeInteger(response.latencyMs)
    || response.latencyMs < 0) {
    throw new Error("rendered response is invalid");
  }
  const provenance = Object.freeze({ ...response.provenance });
  if (Object.values(provenance).some((value) => value.length === 0)) {
    throw new Error("rendered response provenance is incomplete");
  }
  return Object.freeze({ ...response, provenance });
}

/** One immutable, in-memory conversation-turn state object. */
export class ConversationTurn {
  readonly #sessionId: string;
  readonly #turnId: string;
  readonly #turnEpoch: number;
  readonly #status: ConversationTurnStatus;
  readonly #processingBoundary: ProcessingBoundary;
  readonly #inputHash: string | null;
  readonly #ephemeralTranscript: string | null;
  readonly #boundRoute: RouteDecision | null;
  readonly #boundResponse: RenderedResponse | null;

  private constructor(input: {
    sessionId: string;
    turnId: string;
    turnEpoch: number;
    status: ConversationTurnStatus;
    processingBoundary: ProcessingBoundary;
    inputHash: string | null;
    ephemeralTranscript: string | null;
    boundRoute: RouteDecision | null;
    boundResponse: RenderedResponse | null;
  }) {
    this.#sessionId = input.sessionId;
    this.#turnId = input.turnId;
    this.#turnEpoch = input.turnEpoch;
    this.#status = input.status;
    this.#processingBoundary = input.processingBoundary;
    this.#inputHash = input.inputHash;
    this.#ephemeralTranscript = input.ephemeralTranscript;
    this.#boundRoute = input.boundRoute;
    this.#boundResponse = input.boundResponse;
  }

  static open(input: ConversationTurnOpenInput): ConversationTurn {
    assertIdentifier(input.sessionId, "sessionId");
    assertIdentifier(input.turnId, "turnId");
    assertEpoch(input.turnEpoch, "turnEpoch");
    assertBoundary(input.processingBoundary, "processingBoundary");
    return new ConversationTurn({
      ...input,
      status: "Receiving",
      inputHash: null,
      ephemeralTranscript: null,
      boundRoute: null,
      boundResponse: null,
    });
  }

  get snapshot(): ConversationTurnSnapshot {
    return Object.freeze({
      sessionId: this.#sessionId,
      turnId: this.#turnId,
      turnEpoch: this.#turnEpoch,
      status: this.#status,
      processingBoundary: this.#processingBoundary,
      inputHash: this.#inputHash,
      ephemeralTranscript: this.#ephemeralTranscript,
      boundRoute: this.#boundRoute === null ? null : Object.freeze({ ...this.#boundRoute }),
      boundResponse: this.#boundResponse === null ? null : Object.freeze({ ...this.#boundResponse }),
    });
  }

  transcribe(input: TranscribeInput): ConversationTurn {
    if (this.#status !== "Receiving") {
      throw new Error("only a receiving turn can transcribe");
    }
    const length = validatedTranscriptLength(input.transcript);
    if (length === 0 || length > 256) {
      throw new Error("transcript must contain 1..256 Unicode characters");
    }
    if (CREDENTIAL_PATTERNS.some((pattern) => pattern.test(input.transcript))) {
      throw new Error("transcript contains a credential-like value");
    }
    assertBoundary(input.processingBoundary, "processingBoundary");
    assertVersion(input.schemaVersion, "schemaVersion");
    if (!boundaryIsConsented(this.#processingBoundary, input)) {
      throw new Error("transcript boundary consent is invalid");
    }
    return new ConversationTurn({
      sessionId: this.#sessionId,
      turnId: this.#turnId,
      turnEpoch: this.#turnEpoch,
      status: "Routed",
      processingBoundary: this.#processingBoundary,
      inputHash: scopedInputHash(input.transcript, input.schemaVersion),
      ephemeralTranscript: input.transcript,
      boundRoute: null,
      boundResponse: null,
    });
  }

  route(input: { readonly decision: RouteDecision }): ConversationTurn {
    if (this.#status !== "Routed" || this.#inputHash === null) {
      throw new Error("routing requires a validated transcript");
    }
    const route = normalizeRoute(input.decision);
    if (route.inputHash !== this.#inputHash) {
      throw new Error("routing input hash does not match the turn transcript");
    }
    return new ConversationTurn({
      sessionId: this.#sessionId,
      turnId: this.#turnId,
      turnEpoch: this.#turnEpoch,
      status: "Responding",
      processingBoundary: this.#processingBoundary,
      inputHash: this.#inputHash,
      ephemeralTranscript: this.#ephemeralTranscript,
      boundRoute: route,
      boundResponse: null,
    });
  }

  finish(input: { readonly response: RenderedResponse }): ConversationTurn {
    if (this.#status !== "Responding") {
      throw new Error("only a responding turn can finish");
    }
    return new ConversationTurn({
      sessionId: this.#sessionId,
      turnId: this.#turnId,
      turnEpoch: this.#turnEpoch,
      status: "Terminal",
      processingBoundary: this.#processingBoundary,
      inputHash: this.#inputHash,
      ephemeralTranscript: null,
      boundRoute: this.#boundRoute,
      boundResponse: normalizeResponse(input.response),
    });
  }
}
