// DEMO_SCOPE "API kontrakt" — Sessiya / Xabar / Holat / Mashq (+ TZ Ilova B).
export type SessionMode = "companion" | "exercise" | "interpreter" | "checkin";

export type Session = {
  id: string;
  patient_id: string;
  mode: SessionMode;
  started_at: string;
  ended_at?: string | null;
};

export type SessionSummary = {
  caregiver_text: string;
  clinician_text: string;
  attention_needed: boolean;
};

export type Candidate = { key: string; label: string; emoji?: string | null; p?: number };

export type Risk = {
  level: "none" | "low" | "medium" | "high";
  category?: string;
  evidence?: string;
};

export type PatientState = {
  engagement: "low" | "medium" | "high";
  fatigue: number;
  mood: "negative" | "neutral" | "positive" | "unknown";
  mood_conf: number;
  distress: boolean;
  stt_confidence?: number | null;
  explain?: string[];
  inputs?: Record<string, unknown>;
};

export type SuggestedAction =
  | "none"
  | "offer_break"
  | "start_exercise"
  | "notify_caregiver"
  | "notify_clinician"
  | "body_map"
  | null;

export type MessageResponse = {
  patient_message?: { text: string; stt_confidence?: number | null; provider?: string } | null;
  ai_message: { text: string; tts_url: string | null; tts_provider?: string | null };
  needs_confirmation: boolean;
  candidates: Candidate[];
  state?: PatientState | null;
  risk?: Risk | null;
  suggested_action?: SuggestedAction;
};

export type TranscriptMessage = {
  id: string;
  role: "patient" | "ai" | "caregiver" | "system";
  modality: "text" | "voice" | "pictogram";
  text: string;
  audio_url?: string | null;
  stt_confidence?: number | null;
  created_at: string;
  llm_meta?: Record<string, unknown> | null;
};

export type Transcript = {
  session: Session & { summary?: SessionSummary | string | null };
  messages: TranscriptMessage[];
};

export type ExerciseTemplate = {
  id: string;
  category: string;
  subtype: string;
  level: number;
  prompt_text: string;
  prompt_tts_url?: string | null;
  stimulus: {
    emoji?: string | null;
    image?: string | null;
    audio?: string | null;
    text?: string | null;
  };
  cues?: Record<string, string> | null;
};

export type NextExercise =
  | {
      done?: false;
      attempt_id: string;
      template: ExerciseTemplate;
      cue_level: number;
      progress: { index: number; total: number };
    }
  | { done: true; summary: { accuracy?: number; independence?: number; attempts?: number } };

export type SubmitResult = {
  score: number;
  result: "correct" | "partial" | "incorrect";
  recognized_text?: string | null;
  feedback_text: string;
  tts_url?: string | null;
  next_action: "next_item" | "retry_with_cue" | "suggest_break";
  next_cue?: { level: number; text: string; tts_url?: string | null } | null;
};
