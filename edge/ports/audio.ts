export type ProcessingBoundary = "localOnly" | "consentedCloud";

export type AudioSessionStatus = "active" | "degraded" | "closed";

export interface AudioSessionSnapshot {
  sessionId: string;
  status: AudioSessionStatus;
  processingBoundary: ProcessingBoundary;
  turnEpoch: number;
  activeStreamId: string | null;
  startedAtIso: string;
  endedAtIso: string | null;
}

export interface AudioSessionPort {
  open(snapshot: AudioSessionSnapshot): Promise<AudioSessionSnapshot>;
  degrade(sessionId: string, reason: string): Promise<AudioSessionSnapshot>;
  close(sessionId: string, reason: string): Promise<AudioSessionSnapshot>;
}
