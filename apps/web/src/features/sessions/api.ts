import { audioFileName } from "@/features/audio/useRecorder";
import type { FaceBatchItem } from "@/features/face/types";
import { AI_TIMEOUT_MS, apiFetch, apiFetchForm, apiJson } from "@/lib/api";

import type {
  MessageResponse,
  NextExercise,
  PatientState,
  Session,
  SessionMode,
  SessionSummary,
  SubmitResult,
  Transcript,
} from "./types";

export const createSession = (patient_id: string, mode: SessionMode) =>
  apiJson<Session>("/sessions", "POST", { patient_id, mode });

export const endSession = (id: string) =>
  apiJson<{ summary: SessionSummary }>(`/sessions/${id}/end`, "POST", undefined, {
    timeoutMs: AI_TIMEOUT_MS,
  });

export const getSessionState = (id: string) => apiFetch<PatientState>(`/sessions/${id}/state`);
// DEMO_SCOPE: POST /sessions/{id}/face-metrics [Ilova B elements] → {stored} (numbers only, never frames).
export const postFaceMetrics = (id: string, batch: FaceBatchItem[]) =>
  apiJson<{ stored: number }>(`/sessions/${id}/face-metrics`, "POST", batch);
export const getTranscript = (id: string) => apiFetch<Transcript>(`/sessions/${id}/transcript`);

export type MessageInput = { audio: Blob } | { text: string } | { pictogram_key: string };

export function sendMessage(sessionId: string, input: MessageInput): Promise<MessageResponse> {
  const form = new FormData();
  if ("audio" in input) form.append("audio", input.audio, audioFileName(input.audio));
  else if ("text" in input) form.append("text", input.text);
  else form.append("pictogram_key", input.pictogram_key);
  return apiFetchForm<MessageResponse>(`/sessions/${sessionId}/messages`, form);
}

export const confirmCandidate = (sessionId: string, candidate_key: string) =>
  apiJson<MessageResponse>(
    `/sessions/${sessionId}/confirm`,
    "POST",
    { candidate_key },
    {
      timeoutMs: AI_TIMEOUT_MS,
    },
  );

export const getNextExercise = (sessionId: string) =>
  apiFetch<NextExercise>(`/sessions/${sessionId}/exercises/next`, { timeoutMs: AI_TIMEOUT_MS });

export function submitAttempt(
  attemptId: string,
  input: { audio: Blob } | { text: string },
): Promise<SubmitResult> {
  const form = new FormData();
  if ("audio" in input) form.append("audio", input.audio, audioFileName(input.audio));
  else form.append("text", input.text);
  return apiFetchForm<SubmitResult>(`/exercise-attempts/${attemptId}/submit`, form);
}

export const skipAttempt = (attemptId: string) =>
  apiJson<{ ok: boolean }>(`/exercise-attempts/${attemptId}/skip`, "POST");
