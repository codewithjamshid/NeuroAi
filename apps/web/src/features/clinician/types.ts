// DEMO_SCOPE "API kontrakt" — Klinisist / Protokol / Dorilar / Hisobot.
export type ClinicianPatientRow = {
  id: string;
  full_name: string;
  age?: number | null;
  aphasia_type?: string | null;
  open_flags: number;
  last_activity?: string | null;
  adherence_week?: number | null;
};

export type ClinicianSessionRow = {
  id: string;
  mode: string;
  started_at: string;
  ended_at?: string | null;
  summary?:
    | { caregiver_text?: string; clinician_text?: string; attention_needed?: boolean }
    | string
    | null;
  accuracy?: number | null;
  attempts?: number | null;
};

export type ProtocolTemplateItem = {
  kind: "exercise" | "medication" | "checkin";
  category?: string | null;
  level?: number | null;
  frequency?: Record<string, unknown> | null;
  duration_min?: number | null;
};

export type ProtocolTemplate = {
  key: string;
  title: string;
  description?: string | null;
  items: ProtocolTemplateItem[];
};

export type ProtocolItem = {
  id: string;
  kind: string;
  category?: string | null;
  level?: number | null;
  frequency?: Record<string, unknown> | null;
  duration_min?: number | null;
  params?: Record<string, unknown> | null;
};

export type Protocol = {
  id: string;
  title: string;
  status: "active" | "paused" | "done";
  start_date?: string | null;
  items: ProtocolItem[];
};

export type Medication = {
  id: string;
  name: string;
  dose?: string | null;
  schedule?: Record<string, unknown> | null;
  notes?: string | null;
  active?: boolean;
};

export type MedicationCreate = {
  name: string;
  dose?: string;
  schedule?: { times: string[] };
  notes?: string;
};

export type Report = {
  id: string;
  content_md: string;
  metrics?: Record<string, unknown> | null;
  generated_by?: string | null;
  period_start: string;
  period_end: string;
  created_at?: string;
};
