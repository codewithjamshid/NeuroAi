import type { Interpretation } from "@/features/patients/types";
import type { PatientState } from "@/features/sessions/types";

// DEMO_SCOPE "API kontrakt" — Parvarishchi.
export type CaregiverToday = {
  state?: PatientState | null;
  mood_self?: number | null;
  exercises_done: number;
  exercises_planned: number;
  last_interpretations: Interpretation[];
  flags_open: number;
  tips_cached?: string[] | null;
};

export type TipsResponse = { tips: string[] };
export type TelegramLink = { code: string; bot_username?: string | null };
export type TelegramStatus = { linked: boolean };
