// Pure, DOM-free face metrics (TZ §5.1, §7.3). Deterministic and explainable: code computes,
// the LLM only reads the result. Verified by scripts/face-metrics-check (see report).
import type {
  Blendshapes,
  ExerciseKey,
  ExerciseResultCard,
  ExprHint,
  FaceBatchItem,
  FrameMeasure,
  PalsySide,
  Point,
  RepState,
  RestPoints,
} from "./types";

export const HEAD_ANGLE_LIMIT_DEG = 25;
export const ACTIVE_PAIR_MIN = 0.25;
export const ASYM_FLOOR = 0.1;
export const EXCURSION_FLOOR = 0.02;
export const SMILE_ACTIVE_MIN = 0.03;
export const REP_ON = 0.5;
export const REP_OFF = 0.2;
export const REP_MIN_HOLD_MS = 500;
export const HOLD_TARGET_MS = 3000;
export const REPS_TARGET = 5;
export const ATTENTION_WINDOW_MS = 10_000;

// TZ §5.1 paired blendshapes (canonical MediaPipe / ARKit names).
export const PAIRED_BLENDSHAPES = [
  "mouthSmile",
  "browOuterUp",
  "eyeBlink",
  "eyeSquint",
  "cheekSquint",
  "mouthPress",
  "mouthFrown",
  "mouthStretch",
  "mouthUpperUp",
  "mouthLowerDown",
  "noseSneer",
  "mouthDimple",
] as const;

// The 52 canonical blendshapes (for blendshapes_avg).
export const BLENDSHAPE_NAMES = [
  "_neutral",
  "browDownLeft",
  "browDownRight",
  "browInnerUp",
  "browOuterUpLeft",
  "browOuterUpRight",
  "cheekPuff",
  "cheekSquintLeft",
  "cheekSquintRight",
  "eyeBlinkLeft",
  "eyeBlinkRight",
  "eyeLookDownLeft",
  "eyeLookDownRight",
  "eyeLookInLeft",
  "eyeLookInRight",
  "eyeLookOutLeft",
  "eyeLookOutRight",
  "eyeLookUpLeft",
  "eyeLookUpRight",
  "eyeSquintLeft",
  "eyeSquintRight",
  "eyeWideLeft",
  "eyeWideRight",
  "jawForward",
  "jawLeft",
  "jawOpen",
  "jawRight",
  "mouthClose",
  "mouthDimpleLeft",
  "mouthDimpleRight",
  "mouthFrownLeft",
  "mouthFrownRight",
  "mouthFunnel",
  "mouthLeft",
  "mouthLowerDownLeft",
  "mouthLowerDownRight",
  "mouthPressLeft",
  "mouthPressRight",
  "mouthPucker",
  "mouthRight",
  "mouthRollLower",
  "mouthRollUpper",
  "mouthShrugLower",
  "mouthShrugUpper",
  "mouthSmileLeft",
  "mouthSmileRight",
  "mouthStretchLeft",
  "mouthStretchRight",
  "mouthUpperUpLeft",
  "mouthUpperUpRight",
  "noseSneerLeft",
  "noseSneerRight",
] as const;

// Exercise → blendshape signal (paired → mean(L,R); single → itself).
export const EXERCISE_SIGNAL: Record<ExerciseKey, { name: string; paired: boolean }> = {
  face_smile: { name: "mouthSmile", paired: true },
  face_brows: { name: "browOuterUp", paired: true },
  face_eyes: { name: "eyeBlink", paired: true },
  face_pucker: { name: "mouthPucker", paired: false },
  face_cheeks: { name: "cheekPuff", paired: false },
};

export const EXERCISE_ORDER: ExerciseKey[] = [
  "face_smile",
  "face_brows",
  "face_eyes",
  "face_pucker",
  "face_cheeks",
];

// Landmark indices (MediaPipe Face Mesh; L = subject's left = image right when not mirrored).
export const LM = {
  eyeOuterR: 33,
  eyeOuterL: 263,
  mouthR: 61,
  mouthL: 291,
  browR: 105,
  browL: 334,
  eyeUpperL: 386,
  eyeLowerL: 374,
  eyeUpperR: 159,
  eyeLowerR: 145,
} as const;

export const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
export const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const dist = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

export function bs(b: Blendshapes, name: string): number {
  return b[name] ?? 0;
}

// asym_k = |L−R| / max(L, R, 0.10); only pairs with max(L,R) ≥ 0.25 are "active".
export function pairAsymmetry(l: number, r: number): number {
  return Math.abs(l - r) / Math.max(l, r, ASYM_FLOOR);
}

export function blendshapeAsymmetry(b: Blendshapes): {
  pairs: { name: string; l: number; r: number; asym: number; active: boolean }[];
  activeMean: number | null;
} {
  const pairs = PAIRED_BLENDSHAPES.map((name) => {
    const l = bs(b, `${name}Left`);
    const r = bs(b, `${name}Right`);
    return { name, l, r, asym: pairAsymmetry(l, r), active: Math.max(l, r) >= ACTIVE_PAIR_MIN };
  });
  const active = pairs.filter((p) => p.active).map((p) => p.asym);
  return { pairs, activeMean: active.length ? mean(active) : null };
}

// Roll correction via eye corners (33 ↔ 263) and normalisation by IOD. `aspect` = width/height of
// the frame: MediaPipe landmarks are normalised per axis, so x is rescaled before measuring.
export type FaceFrame = { iod: number; roll: number; p: (i: number) => Point };

export function faceFrame(landmarks: Point[], aspect = 1): FaceFrame | null {
  if (landmarks.length < 468) return null;
  const raw = (i: number): Point => ({ x: landmarks[i].x * aspect, y: landmarks[i].y });
  const eR = raw(LM.eyeOuterR);
  const eL = raw(LM.eyeOuterL);
  const iod = dist(eR, eL);
  if (!(iod > 1e-6)) return null;
  const roll = Math.atan2(eL.y - eR.y, eL.x - eR.x);
  const cx = (eR.x + eL.x) / 2;
  const cy = (eR.y + eL.y) / 2;
  const c = Math.cos(-roll);
  const s = Math.sin(-roll);
  const p = (i: number): Point => {
    const q = raw(i);
    const dx = q.x - cx;
    const dy = q.y - cy;
    return { x: (dx * c - dy * s) / iod, y: (dx * s + dy * c) / iod };
  };
  return { iod, roll, p };
}

export type LandmarkMeasures = {
  mouthL: Point;
  mouthR: Point;
  excursionL: number | null;
  excursionR: number | null;
  smileAsym: number | null; // null when no rest points or excursion below SMILE_ACTIVE_MIN
  browL: number;
  browR: number;
  browAsym: number;
  earL: number;
  earR: number;
  eyeAsym: number;
};

export function landmarkMeasures(frame: FaceFrame, rest?: RestPoints | null): LandmarkMeasures {
  const mouthL = frame.p(LM.mouthL);
  const mouthR = frame.p(LM.mouthR);
  let excursionL: number | null = null;
  let excursionR: number | null = null;
  let smileAsym: number | null = null;
  if (rest) {
    excursionL = dist(mouthL, rest.mouthL);
    excursionR = dist(mouthR, rest.mouthR);
    if (Math.max(excursionL, excursionR) >= SMILE_ACTIVE_MIN) {
      smileAsym =
        Math.abs(excursionL - excursionR) / Math.max(excursionL, excursionR, EXCURSION_FLOOR);
    }
  }
  // After roll correction both eye corners sit on y = 0; brow height = eye line − brow y.
  const browL = frame.p(LM.eyeOuterL).y - frame.p(LM.browL).y;
  const browR = frame.p(LM.eyeOuterR).y - frame.p(LM.browR).y;
  const browAsym = Math.abs(browL - browR) / Math.max(browL, browR, EXCURSION_FLOOR);
  const earL = dist(frame.p(LM.eyeUpperL), frame.p(LM.eyeLowerL));
  const earR = dist(frame.p(LM.eyeUpperR), frame.p(LM.eyeLowerR));
  const eyeAsym = Math.abs(earL - earR) / Math.max(earL, earR, EXCURSION_FLOOR);
  return {
    mouthL,
    mouthR,
    excursionL,
    excursionR,
    smileAsym,
    browL,
    browR,
    browAsym,
    earL,
    earR,
    eyeAsym,
  };
}

// FSI = 1 − clamp(mean(active asym_k ∪ smile_asym ∪ brow_asym), 0, 1)
export function computeFsi(
  activeAsym: number | null,
  smileAsym: number | null,
  browAsym: number | null,
): number {
  const parts = [activeAsym, smileAsym, browAsym].filter((v): v is number => v !== null);
  if (!parts.length) return 1;
  return 1 - clamp(mean(parts), 0, 1);
}

// Yaw/pitch (degrees) from the 4×4 facial transformation matrix (column-major, like the
// MediaPipe C++ MatrixData). The face's forward axis is the third column of the rotation part.
export function headPose(matrix: number[] | null | undefined): { yaw: number; pitch: number } {
  if (!matrix || matrix.length < 12) return { yaw: 0, pitch: 0 };
  const fx = matrix[8];
  const fy = matrix[9];
  const fz = Math.abs(matrix[10]);
  const deg = 180 / Math.PI;
  return { yaw: Math.atan2(fx, fz) * deg, pitch: Math.atan2(fy, fz) * deg };
}

export function headInRange(yaw: number, pitch: number): boolean {
  return Math.abs(yaw) <= HEAD_ANGLE_LIMIT_DEG && Math.abs(pitch) <= HEAD_ANGLE_LIMIT_DEG;
}

// Expression hint from the healthy side only (palsy side must not read as "sad/angry").
export function exprHint(b: Blendshapes, palsy: PalsySide): ExprHint {
  const side = (name: string): number => {
    const l = bs(b, `${name}Left`);
    const r = bs(b, `${name}Right`);
    if (palsy === "left") return r;
    if (palsy === "right") return l;
    return (l + r) / 2;
  };
  const conf = (v: number) => Math.min(0.6, Math.round(v * 100) / 100);
  const squint = side("eyeSquint");
  const sneer = side("noseSneer");
  if (squint >= 0.5 && sneer >= 0.3)
    return { label: "grimace", conf: conf(Math.min(squint, sneer)) };
  const frown = side("mouthFrown");
  const innerUp = bs(b, "browInnerUp");
  if (frown >= 0.3 && innerUp >= 0.3)
    return { label: "frown", conf: conf(Math.min(frown, innerUp)) };
  const smile = side("mouthSmile");
  if (smile >= 0.5) return { label: "happy", conf: conf(smile) };
  return { label: "neutral", conf: 0.4 };
}

// fatigue = clamp(0.5·(1 − EAR/EAR_base) + 0.3·(blink/blink_base − 1) + 0.2·pitch_down, 0, 1)
export function fatigueProxy(input: {
  earNow: number | null;
  earBase: number | null;
  blinkRateNow: number | null;
  blinkRateBase: number | null;
  pitch: number;
}): number {
  const earTerm =
    input.earNow !== null && input.earBase && input.earBase > 0
      ? 1 - input.earNow / input.earBase
      : 0;
  const blinkTerm =
    input.blinkRateNow !== null && input.blinkRateBase && input.blinkRateBase > 0
      ? input.blinkRateNow / input.blinkRateBase - 1
      : 0;
  // Head tilted down = forward axis pointing below the camera axis (negative pitch here).
  const pitchDown = clamp(Math.max(0, -input.pitch) / HEAD_ANGLE_LIMIT_DEG, 0, 1);
  return clamp(0.5 * earTerm + 0.3 * blinkTerm + 0.2 * pitchDown, 0, 1);
}

// attention = (face present ratio) × (|yaw|,|pitch| ≤ 25° ratio among present) over the window.
export function attentionOf(frames: { present: boolean; inRange: boolean }[]): number {
  if (!frames.length) return 0;
  const present = frames.filter((f) => f.present);
  if (!present.length) return 0;
  const presentRatio = present.length / frames.length;
  const inRangeRatio = present.filter((f) => f.inRange).length / present.length;
  return clamp(presentRatio * inRangeRatio, 0, 1);
}

// Signal s(t) for the exercise: mean(L,R) for paired shapes, the shape itself otherwise.
export function exerciseSignal(b: Blendshapes, key: ExerciseKey): number {
  const { name, paired } = EXERCISE_SIGNAL[key];
  if (!paired) return bs(b, name);
  return (bs(b, `${name}Left`) + bs(b, `${name}Right`)) / 2;
}

export function exerciseSides(b: Blendshapes, key: ExerciseKey): { l: number; r: number } | null {
  const { name, paired } = EXERCISE_SIGNAL[key];
  if (!paired) return null;
  return { l: bs(b, `${name}Left`), r: bs(b, `${name}Right`) };
}

export const initialRepState = (): RepState => ({
  phase: "idle",
  reps: 0,
  holdStart: null,
  holdMs: 0,
  holdMax: 0,
  amplitudes: [],
  holdDurations: [],
  signal: 0,
});

// s ≥ 0.5 for ≥ 0.5 s → "holding"; then s ≤ 0.2 → +1 rep. Amplitude = max s during the hold.
export function stepRepCounter(state: RepState, s: number, tMs: number): RepState {
  if (state.phase === "idle") {
    if (s >= REP_ON) {
      const holdStart = state.holdStart ?? tMs;
      const holdMs = tMs - holdStart;
      const holdMax = Math.max(state.holdMax, s);
      if (holdMs >= REP_MIN_HOLD_MS) {
        return { ...state, phase: "holding", holdStart, holdMs, holdMax, signal: s };
      }
      return { ...state, holdStart, holdMs, holdMax, signal: s };
    }
    // dropped before the minimum hold → reset the candidate
    return { ...state, holdStart: null, holdMs: 0, holdMax: 0, signal: s };
  }
  // holding
  if (s <= REP_OFF) {
    return {
      phase: "idle",
      reps: state.reps + 1,
      holdStart: null,
      holdMs: 0,
      holdMax: 0,
      amplitudes: [...state.amplitudes, state.holdMax],
      holdDurations: [...state.holdDurations, state.holdMs],
      signal: s,
    };
  }
  return {
    ...state,
    holdMs: tMs - (state.holdStart ?? tMs),
    holdMax: Math.max(state.holdMax, s),
    signal: s,
  };
}

export type MeasureInput = {
  t: number;
  landmarks: Point[] | null;
  blendshapes: Blendshapes | null;
  matrix: number[] | null;
  aspect: number;
  rest: RestPoints | null;
  palsy: PalsySide;
};

const NEUTRAL: ExprHint = { label: "neutral", conf: 0.4 };

export function measureFrame(input: MeasureInput): FrameMeasure {
  const empty: FrameMeasure = {
    t: input.t,
    present: false,
    yaw: 0,
    pitch: 0,
    inRange: false,
    measured: false,
    fsi: null,
    activeAsym: null,
    smileAsym: null,
    browAsym: null,
    eyeAsym: null,
    ear: null,
    earL: null,
    earR: null,
    mouthOpen: null,
    mouthL: null,
    mouthR: null,
    blendshapes: null,
    expr: NEUTRAL,
  };
  const frame = input.landmarks ? faceFrame(input.landmarks, input.aspect) : null;
  if (!frame || !input.blendshapes) return empty;
  const { yaw, pitch } = headPose(input.matrix);
  const inRange = headInRange(yaw, pitch);
  const b = input.blendshapes;
  const expr = exprHint(b, input.palsy);
  if (!inRange) {
    return { ...empty, present: true, yaw, pitch, blendshapes: b, expr };
  }
  const lm = landmarkMeasures(frame, input.rest);
  const { activeMean } = blendshapeAsymmetry(b);
  const fsi = computeFsi(activeMean, lm.smileAsym, lm.browAsym);
  return {
    t: input.t,
    present: true,
    yaw,
    pitch,
    inRange: true,
    measured: true,
    fsi,
    activeAsym: activeMean,
    smileAsym: lm.smileAsym,
    browAsym: lm.browAsym,
    eyeAsym: lm.eyeAsym,
    ear: (lm.earL + lm.earR) / 2,
    earL: lm.earL,
    earR: lm.earR,
    mouthOpen: bs(b, "jawOpen"),
    mouthL: lm.mouthL,
    mouthR: lm.mouthR,
    blendshapes: b,
    expr,
  };
}

const meanOf = (xs: (number | null)[]): number | null => {
  const v = xs.filter((x): x is number => x !== null && Number.isFinite(x));
  return v.length ? mean(v) : null;
};

export function averageBlendshapes(list: Blendshapes[]): Blendshapes {
  const out: Blendshapes = {};
  for (const name of BLENDSHAPE_NAMES) {
    out[name] = list.length ? round4(mean(list.map((b) => bs(b, name)))) : 0;
  }
  return out;
}

export const round2 = (v: number) => Math.round(v * 100) / 100;
export const round4 = (v: number) => Math.round(v * 10_000) / 10_000;

// 1 Hz aggregation of ~15 frames → Ilova B element. Unmeasurable values fall back to `prev`.
export function aggregateSecond(input: {
  frames: FrameMeasure[];
  ts: number; // epoch seconds
  reps: number;
  attention: number;
  fatigue: number;
  restAsym: number | null;
  prev: FaceBatchItem | null;
}): FaceBatchItem {
  const { frames, prev } = input;
  const present = frames.filter((f) => f.present);
  const measured = frames.filter((f) => f.measured);
  const facePresent = frames.length > 0 && present.length >= frames.length / 2;
  const pick = (v: number | null, key: keyof FaceBatchItem, dflt: number): number => {
    if (v !== null) return round2(v);
    const p = prev ? prev[key] : null;
    return typeof p === "number" ? p : dflt;
  };
  const labels = present.map((f) => f.expr.label);
  let expr: ExprHint = prev?.expr_hint ?? NEUTRAL;
  if (labels.length) {
    const counts = new Map<string, number>();
    for (const l of labels) counts.set(l, (counts.get(l) ?? 0) + 1);
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
    const confs = present.filter((f) => f.expr.label === top).map((f) => f.expr.conf);
    expr = { label: top as ExprHint["label"], conf: round2(Math.min(0.6, mean(confs))) };
  }
  return {
    ts: input.ts,
    face_present: facePresent,
    yaw: pick(meanOf(present.map((f) => f.yaw)), "yaw", 0),
    pitch: pick(meanOf(present.map((f) => f.pitch)), "pitch", 0),
    fsi: pick(meanOf(measured.map((f) => f.fsi)), "fsi", 1),
    rest_asym: round2(input.restAsym ?? prev?.rest_asym ?? 0),
    smile_asym: pick(meanOf(measured.map((f) => f.smileAsym)), "smile_asym", 0),
    brow_asym: pick(meanOf(measured.map((f) => f.browAsym)), "brow_asym", 0),
    eye_asym: pick(meanOf(measured.map((f) => f.eyeAsym)), "eye_asym", 0),
    mouth_open: pick(meanOf(measured.map((f) => f.mouthOpen)), "mouth_open", 0),
    attention: round2(input.attention),
    fatigue_proxy: round2(input.fatigue),
    expr_hint: expr,
    blendshapes_avg: present.length
      ? averageBlendshapes(present.map((f) => f.blendshapes as Blendshapes))
      : (prev?.blendshapes_avg ?? averageBlendshapes([])),
    reps: input.reps,
  };
}

// §7.3: score = 0.5·(reps/target) + 0.3·mean_amplitude + 0.2·FSI_exercise; correct ≥ 0.7.
export function exerciseScore(
  reps: number,
  target: number,
  meanAmp: number,
  fsi: number | null,
): { score: number; result: ExerciseResultCard["result"] } {
  const score = clamp(
    0.5 * Math.min(1, reps / Math.max(1, target)) + 0.3 * clamp(meanAmp, 0, 1) + 0.2 * (fsi ?? 1),
    0,
    1,
  );
  const result = score >= 0.7 ? "correct" : score >= 0.4 ? "partial" : "incorrect";
  return { score, result };
}

// Which side moved less during holds (paired exercises only).
export function weakerSide(sideSamples: { l: number; r: number }[]): {
  side: "left" | "right" | null;
  asym: number;
} {
  if (!sideSamples.length) return { side: null, asym: 0 };
  const l = mean(sideSamples.map((s) => s.l));
  const r = mean(sideSamples.map((s) => s.r));
  const asym = pairAsymmetry(l, r);
  if (asym < 0.3) return { side: null, asym };
  return { side: l < r ? "left" : "right", asym };
}
