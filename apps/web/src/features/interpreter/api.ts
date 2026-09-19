import { audioFileName } from "@/features/audio/useRecorder";
import { AI_TIMEOUT_MS, apiFetch, apiFetchForm, apiJson } from "@/lib/api";

import type { Board, ConfirmResponse, GuessResponse } from "./types";

export function interpreterGuess(
  patientId: string,
  input: { audio: Blob } | { text: string },
  sessionId?: string | null,
): Promise<GuessResponse> {
  const form = new FormData();
  form.append("patient_id", patientId);
  if (sessionId) form.append("session_id", sessionId);
  if ("audio" in input) form.append("audio", input.audio, audioFileName(input.audio));
  else form.append("text", input.text);
  return apiFetchForm<GuessResponse>("/interpreter/guess", form);
}

export const interpreterConfirm = (body: {
  interpretation_id: string;
  candidate_key?: string;
  custom_text?: string;
}) => apiJson<ConfirmResponse>("/interpreter/confirm", "POST", body, { timeoutMs: AI_TIMEOUT_MS });

export const getBoard = (patientId: string) =>
  apiFetch<Board>(`/interpreter/board?patient_id=${encodeURIComponent(patientId)}`);
