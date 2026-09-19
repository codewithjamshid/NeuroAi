// DEMO_SCOPE "API kontrakt" — Patients / Today / Mood / Dashboard / Red flags.
export type Patient = {
  id: string;
  full_name: string;
  birth_year?: number | null;
  sex?: string | null;
  stroke_date?: string | null;
  affected_side?: string | null;
  aphasia_type?: string | null;
  dialect?: string | null;
  interests?: string[] | null;
  family_members?: { name: string; relation: string }[] | null;
  habits?: string[] | null;
  clinician_id?: string | null;
};

export type PatientCreate = {
  full_name: string;
  birth_year?: number | null;
  sex?: string | null;
  stroke_date?: string | null;
  affected_side?: string | null;
  aphasia_type?: string | null;
  dialect?: string | null;
  interests?: string[];
  family_members?: { name: string; relation: string }[];
  consent: { scopes: Record<string, boolean> };
};

export type TodayItem = {
  id: string;
  kind: "exercise" | "medication" | "checkin";
  title: string;
  category?: string | null;
  level?: number | null;
  duration_min?: number | null;
  time?: string | null;
  done: boolean;
  protocol_item_id?: string | null;
  medication_id?: string | null;
};

export type TodayResponse = { date: string; items: TodayItem[]; mood_self?: number | null };

export type MoodTrendPoint = { date: string; self_score?: number | null; valence?: number | null };

export type RedFlagStatus = "open" | "acknowledged" | "resolved";
export type RedFlag = {
  id: string;
  category: string;
  severity: "low" | "medium" | "high";
  evidence?: string | null;
  detector?: string | null;
  status: RedFlagStatus;
  session_id?: string | null;
  created_at: string;
  note?: string | null;
};

export type DashboardDay = {
  date: string;
  speech_accuracy?: number | null;
  independence?: number | null;
  avg_cue_level?: number | null;
  fsi?: number | null;
  mood_self?: number | null;
  valence?: number | null;
  adherence_exercise?: number | null;
  adherence_medication?: number | null;
};

export type Dashboard = {
  days: DashboardDay[];
  flags: RedFlag[];
  adherence_week: { exercise?: number | null; medication?: number | null };
  sessions_count: number;
  fsi_base?: number | null;
};

export type Interpretation = {
  id: string;
  raw_transcript?: string | null;
  chosen?: string | null;
  spoken_text?: string | null;
  family_note?: string | null;
  confirmed_by?: string | null;
  created_at: string;
};
