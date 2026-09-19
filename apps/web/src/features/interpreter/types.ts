// DEMO_SCOPE "API kontrakt" — Tarjimon.
export type GuessCandidate = { key: string; label: string; emoji?: string | null; p?: number };

export type GuessResponse = {
  interpretation_id: string;
  raw_transcript?: string | null;
  confidence?: number | null;
  candidates: GuessCandidate[];
  board_suggested: boolean;
};

export type ConfirmResponse = {
  spoken_text: string;
  tts_url?: string | null;
  family_note?: string | null;
  follow_up?: "none" | "body_map" | "yes_no" | null;
};

export type BoardItem = {
  key: string;
  label: string;
  emoji?: string | null;
  group?: string | null;
};
export type BodyZone = { key: string; label: string; emoji?: string | null };
export type Board = { items: BoardItem[]; body_map: BodyZone[] };
