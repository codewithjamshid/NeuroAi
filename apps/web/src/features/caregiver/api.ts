import { AI_TIMEOUT_MS, apiFetch, apiJson } from "@/lib/api";

import type { CaregiverToday, TelegramLink, TelegramStatus, TipsResponse } from "./types";

export const getCaregiverToday = (patientId: string) =>
  apiFetch<CaregiverToday>(`/caregiver/patients/${patientId}/today`);
export const getTips = (patientId: string) =>
  apiFetch<TipsResponse>(`/caregiver/patients/${patientId}/tips`, { timeoutMs: AI_TIMEOUT_MS });
export const telegramLink = () => apiJson<TelegramLink>("/notifications/telegram/link", "POST");
export const telegramStatus = () => apiFetch<TelegramStatus>("/notifications/telegram/status");
