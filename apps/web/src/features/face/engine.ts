// Runtime state machine over per-frame measurements: attention window, blink/fatigue,
// calibration collection, rep counting and the 1 Hz Ilova B aggregator. No DOM access.
import type { RawFrame } from "./mediapipe";
import {
  ATTENTION_WINDOW_MS,
  aggregateSecond,
  attentionOf,
  bs,
  exerciseSides,
  exerciseSignal,
  fatigueProxy,
  initialRepState,
  mean,
  measureFrame,
  stepRepCounter,
} from "./metrics";
import type {
  ExerciseKey,
  FaceBaseline,
  FaceBatchItem,
  FrameMeasure,
  PalsySide,
  RepState,
  RestPoints,
} from "./types";

export type EngineSnapshot = {
  frame: FrameMeasure | null;
  rep: RepState;
  attention: number;
  fatigue: number;
  calibProgress: number | null; // null when not calibrating
  exercise: ExerciseKey | null;
  exerciseFsi: number | null;
};

export type ExerciseStats = {
  rep: RepState;
  fsi: number | null;
  sides: { l: number; r: number }[];
};

const BLINK_WINDOW_MS = 30_000;
const EAR_WINDOW_MS = 5_000;

export class FaceEngine {
  rest: RestPoints | null = null;
  baseline: FaceBaseline | null = null;
  palsy: PalsySide = null;
  onSecond: ((item: FaceBatchItem) => void) | null = null;
  onCalibrated: ((frames: FrameMeasure[], blinks: number, ms: number) => void) | null = null;

  private frame: FrameMeasure | null = null;
  private window: { t: number; present: boolean; inRange: boolean }[] = [];
  private bucket: FrameMeasure[] = [];
  private bucketStart = -1;
  private prevItem: FaceBatchItem | null = null;
  private blinkOn = false;
  private blinkTimes: number[] = [];
  private earHist: { t: number; ear: number }[] = [];
  private attention = 0;
  private fatigue = 0;
  private startT = -1;
  private lastT = -1;
  private calib: { frames: FrameMeasure[]; ms: number; blinks: number; targetMs: number } | null =
    null;
  private exercise: ExerciseKey | null = null;
  private rep: RepState = initialRepState();
  private exFsi: number[] = [];
  private exSides: { l: number; r: number }[] = [];

  startCalibration(targetMs: number) {
    this.calib = { frames: [], ms: 0, blinks: 0, targetMs };
  }

  cancelCalibration() {
    this.calib = null;
  }

  setExercise(key: ExerciseKey | null) {
    this.exercise = key;
    this.rep = initialRepState();
    this.exFsi = [];
    this.exSides = [];
  }

  exerciseStats(): ExerciseStats {
    return {
      rep: this.rep,
      fsi: this.exFsi.length ? mean(this.exFsi) : null,
      sides: this.exSides,
    };
  }

  handle(raw: RawFrame) {
    const m = measureFrame({
      t: raw.t,
      landmarks: raw.landmarks,
      blendshapes: raw.blendshapes,
      matrix: raw.matrix,
      aspect: raw.aspect,
      rest: this.rest,
      palsy: this.palsy,
    });
    if (this.startT < 0) this.startT = m.t;
    const dt = this.lastT < 0 ? 0 : Math.min(200, Math.max(0, m.t - this.lastT));
    this.lastT = m.t;
    this.frame = m;

    // attention: last 10 s
    this.window.push({ t: m.t, present: m.present, inRange: m.inRange });
    while (this.window.length && m.t - this.window[0].t > ATTENTION_WINDOW_MS) this.window.shift();
    this.attention = attentionOf(this.window);

    // blinks (rising edge of mean eyeBlink ≥ 0.5)
    let blinkEdge = false;
    if (m.blendshapes) {
      const s = (bs(m.blendshapes, "eyeBlinkLeft") + bs(m.blendshapes, "eyeBlinkRight")) / 2;
      if (s >= 0.5 && !this.blinkOn) {
        this.blinkOn = true;
        blinkEdge = true;
        this.blinkTimes.push(m.t);
      } else if (s < 0.3) {
        this.blinkOn = false;
      }
    }
    while (this.blinkTimes.length && m.t - this.blinkTimes[0] > BLINK_WINDOW_MS) {
      this.blinkTimes.shift();
    }
    if (m.ear !== null) this.earHist.push({ t: m.t, ear: m.ear });
    while (this.earHist.length && m.t - this.earHist[0].t > EAR_WINDOW_MS) this.earHist.shift();

    // fatigue proxy vs baseline
    const elapsedMin = Math.max(10_000, Math.min(BLINK_WINDOW_MS, m.t - this.startT)) / 60_000;
    this.fatigue = fatigueProxy({
      earNow: this.earHist.length ? mean(this.earHist.map((e) => e.ear)) : null,
      earBase: this.baseline?.earBase ?? null,
      blinkRateNow: this.blinkTimes.length / elapsedMin,
      blinkRateBase: this.baseline?.blinkRateBase ?? null,
      pitch: m.pitch,
    });

    // calibration: accumulate measured time only
    if (this.calib && m.measured) {
      this.calib.frames.push(m);
      this.calib.ms += dt;
      if (blinkEdge) this.calib.blinks++;
      if (this.calib.ms >= this.calib.targetMs) {
        const c = this.calib;
        this.calib = null;
        this.onCalibrated?.(c.frames, c.blinks, c.ms);
      }
    }

    // exercise reps
    if (this.exercise && m.measured && m.blendshapes) {
      const s = exerciseSignal(m.blendshapes, this.exercise);
      this.rep = stepRepCounter(this.rep, s, m.t);
      if (this.rep.phase === "holding") {
        const sides = exerciseSides(m.blendshapes, this.exercise);
        if (sides) this.exSides.push(sides);
      }
      if (m.fsi !== null) this.exFsi.push(m.fsi);
    }

    // 1 Hz aggregation
    if (this.bucketStart < 0) this.bucketStart = m.t;
    this.bucket.push(m);
    if (m.t - this.bucketStart >= 1000) this.flushSecond();
  }

  flushSecond() {
    if (!this.bucket.length) return;
    const item = aggregateSecond({
      frames: this.bucket,
      ts: Math.round(Date.now()) / 1000,
      reps: this.rep.reps,
      attention: this.attention,
      fatigue: this.fatigue,
      restAsym: this.baseline?.restAsym ?? null,
      prev: this.prevItem,
    });
    this.prevItem = item;
    this.bucket = [];
    this.bucketStart = -1;
    this.onSecond?.(item);
  }

  snapshot(): EngineSnapshot {
    return {
      frame: this.frame,
      rep: this.rep,
      attention: this.attention,
      fatigue: this.fatigue,
      calibProgress: this.calib ? Math.min(1, this.calib.ms / this.calib.targetMs) : null,
      exercise: this.exercise,
      exerciseFsi: this.exFsi.length ? mean(this.exFsi) : null,
    };
  }
}
