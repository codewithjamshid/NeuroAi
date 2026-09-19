// Face exercise (TZ §5.1, §7.3, Ilova B). Only numbers leave the browser — never frames.
export type Point = { x: number; y: number; z?: number };

export type Blendshapes = Record<string, number>;

export type ExerciseKey = "face_smile" | "face_brows" | "face_eyes" | "face_pucker" | "face_cheeks";

export type ExprLabel = "happy" | "frown" | "grimace" | "neutral";
export type ExprHint = { label: ExprLabel; conf: number };

// Patient.affected_side from GET /patients/{id}; anything else → both sides are used.
export type PalsySide = "left" | "right" | null;

// Rest landmarks in the "face frame": roll-corrected, centred on the eye midpoint, ÷ IOD.
export type RestPoints = { mouthL: Point; mouthR: Point };

export type FaceBaseline = {
  version: 1;
  patientId: string;
  createdAt: number; // epoch ms
  rest: RestPoints;
  fsiBase: number;
  restAsym: number;
  earBase: number;
  blinkRateBase: number; // blinks / minute
};

// Per-frame measurement (≈15 fps). `measured` = face present and head within ±25°.
export type FrameMeasure = {
  t: number; // ms (performance.now)
  present: boolean;
  yaw: number;
  pitch: number;
  inRange: boolean;
  measured: boolean;
  fsi: number | null;
  activeAsym: number | null; // mean of active paired-blendshape asymmetries
  smileAsym: number | null;
  browAsym: number | null;
  eyeAsym: number | null;
  ear: number | null; // mean(ear_L, ear_R)
  earL: number | null;
  earR: number | null;
  mouthOpen: number | null; // jawOpen
  mouthL: Point | null; // face-frame coords (for calibration)
  mouthR: Point | null;
  blendshapes: Blendshapes | null;
  expr: ExprHint;
};

export type RepPhase = "idle" | "holding";

export type RepState = {
  phase: RepPhase;
  reps: number;
  holdStart: number | null; // ms
  holdMs: number; // current hold duration
  holdMax: number; // max signal in the current hold
  amplitudes: number[]; // max signal of every counted rep
  holdDurations: number[]; // ms of every counted rep
  signal: number;
};

// Ilova B batch element (+ mouth_open, reps).
export type FaceBatchItem = {
  ts: number; // epoch seconds
  face_present: boolean;
  yaw: number;
  pitch: number;
  fsi: number;
  rest_asym: number;
  smile_asym: number;
  brow_asym: number;
  eye_asym: number;
  mouth_open: number;
  attention: number;
  fatigue_proxy: number;
  expr_hint: ExprHint;
  blendshapes_avg: Blendshapes;
  reps: number;
};

export type ExerciseResultCard = {
  key: ExerciseKey;
  reps: number;
  target: number;
  meanAmp: number;
  fsi: number | null; // mean FSI over the exercise's measured frames
  score: number;
  result: "correct" | "partial" | "incorrect";
  weakerSide: "left" | "right" | null; // by blendshape amplitude during holds
  sideAsym: number; // |L−R|/max during holds (0 for single-sided signals)
};

export type CameraErrorCode = "cam_denied" | "no_cam" | "not_supported" | "model_failed";
