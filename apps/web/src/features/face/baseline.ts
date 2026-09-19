// Personal baseline (TZ §5.1 kalibrovka) in localStorage: neuroai.face.baseline.<patientId>.
import { mean } from "./metrics";
import type { FaceBaseline, FrameMeasure } from "./types";

export const BASELINE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
export const CALIBRATION_MS = 10_000;

export const baselineKey = (patientId: string) => `neuroai.face.baseline.${patientId}`;

export function loadBaseline(patientId: string): FaceBaseline | null {
  try {
    const raw = window.localStorage.getItem(baselineKey(patientId));
    if (!raw) return null;
    const b = JSON.parse(raw) as Partial<FaceBaseline>;
    if (b.version !== 1 || typeof b.createdAt !== "number" || !b.rest) return null;
    if (Date.now() - b.createdAt > BASELINE_MAX_AGE_MS) return null;
    return b as FaceBaseline;
  } catch {
    return null;
  }
}

export function saveBaseline(b: FaceBaseline): void {
  try {
    window.localStorage.setItem(baselineKey(b.patientId), JSON.stringify(b));
  } catch {
    // storage full / private mode: the baseline still lives in memory for this session
  }
}

export function clearBaseline(patientId: string): void {
  try {
    window.localStorage.removeItem(baselineKey(patientId));
  } catch {
    // ignore
  }
}

export const baselineAgeDays = (b: FaceBaseline) =>
  Math.floor((Date.now() - b.createdAt) / (24 * 60 * 60 * 1000));

// Rest landmarks + FSI_base + EAR_base + blink_rate_base from the calibration frames
// (measured frames only: face present, head within ±25°).
export function buildBaseline(
  patientId: string,
  frames: FrameMeasure[],
  blinks: number,
  durationMs: number,
): FaceBaseline | null {
  const ok = frames.filter((f) => f.measured && f.mouthL && f.mouthR);
  if (ok.length < 5) return null;
  const fsiBase = mean(ok.map((f) => f.fsi as number));
  const minutes = Math.max(durationMs, 1000) / 60_000;
  return {
    version: 1,
    patientId,
    createdAt: Date.now(),
    rest: {
      mouthL: {
        x: mean(ok.map((f) => (f.mouthL as { x: number }).x)),
        y: mean(ok.map((f) => (f.mouthL as { y: number }).y)),
      },
      mouthR: {
        x: mean(ok.map((f) => (f.mouthR as { x: number }).x)),
        y: mean(ok.map((f) => (f.mouthR as { y: number }).y)),
      },
    },
    fsiBase,
    restAsym: 1 - fsiBase,
    earBase: mean(ok.map((f) => f.ear as number)),
    blinkRateBase: Math.max(6, blinks / minutes),
  };
}
