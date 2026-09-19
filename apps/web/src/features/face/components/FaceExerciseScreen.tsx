"use client";

import {
  ArrowRight,
  Camera,
  CameraOff,
  RotateCw,
  ScanFace,
  ShieldCheck,
  SkipForward,
  TriangleAlert,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { BigButton } from "@/components/BigButton";
import { LoadingCard } from "@/components/ErrorCard";
import { ResultBanner } from "@/components/ResultBanner";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatient, usePatientId } from "@/features/patients/hooks";
import { postFaceMetrics } from "@/features/sessions/api";
import { useSessionLifecycle } from "@/features/sessions/hooks";
import { type I18nKey, t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { CALIBRATION_MS, baselineAgeDays, buildBaseline } from "../baseline";
import { speak, stopSpeaking, useFaceBaseline, useFaceTracker, warmInstructions } from "../hooks";
import {
  EXERCISE_ORDER,
  HOLD_TARGET_MS,
  REPS_TARGET,
  REP_ON,
  exerciseScore,
  mean,
  weakerSide,
} from "../metrics";
import type {
  ExerciseKey,
  ExerciseResultCard,
  FaceBatchItem,
  FrameMeasure,
  PalsySide,
} from "../types";

type Step = "camera" | "calibrate" | "exercise" | "summary";

const EMOJI: Record<ExerciseKey, string> = {
  face_smile: "😁",
  face_brows: "🤨",
  face_eyes: "😑",
  face_pucker: "😗",
  face_cheeks: "😙",
};

const BATCH_SIZE = 10;
const pct = (v: number | null | undefined) =>
  v === null || v === undefined ? "—" : `${Math.round(v * 100)} %`;
const signed = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(Math.round(v * 100))}`;

// Patient.affected_side ("left" | "right" | "both" | "unknown" | …) → side used as facial palsy side.
function toPalsy(side: string | null | undefined): PalsySide {
  if (side === "left" || side === "right") return side;
  return null;
}

function feedbackText(card: ExerciseResultCard): string {
  if (card.weakerSide) {
    const strong = card.weakerSide === "left" ? "right" : "left";
    return t("face.feedback.side", {
      strong: t(`side.${strong}` as I18nKey),
      weak: t(`face.side.${card.weakerSide}` as I18nKey),
    });
  }
  if (card.reps < card.target) return t("face.feedback.more_reps");
  if (card.meanAmp < 0.6) return t("face.feedback.amplitude");
  return t("face.feedback.good");
}

// TZ §8.2 /p/exercise/face: big camera, live symmetry 0–100 %, rep counter, instruction.
export function FaceExerciseScreen() {
  const { patientId, isPending: pidPending } = usePatientId();
  const patient = usePatient(patientId);
  const palsy = toPalsy(patient.data?.affected_side);
  const { baseline, save: saveBaseline, clear: clearBaseline } = useFaceBaseline(patientId);

  // Batch buffer. Declared before useSessionLifecycle so its unmount flush runs before /end.
  const batchRef = useRef<FaceBatchItem[]>([]);
  const sessionIdRef = useRef<string | null>(null);
  const flush = useCallback(() => {
    const id = sessionIdRef.current;
    if (!id) {
      batchRef.current = batchRef.current.slice(-60);
      return;
    }
    const items = batchRef.current;
    batchRef.current = [];
    if (items.length) void postFaceMetrics(id, items).catch(() => undefined);
  }, []);
  useEffect(() => () => flush(), [flush]);

  const { session, error: sessionError } = useSessionLifecycle(patientId, "exercise");
  useEffect(() => {
    sessionIdRef.current = session?.id ?? null;
  }, [session]);

  const [step, setStep] = useState<Step>("camera");
  const [exIdx, setExIdx] = useState(0);
  const [results, setResults] = useState<ExerciseResultCard[]>([]);
  const [calibAttempt, setCalibAttempt] = useState(0);
  const [calibFailed, setCalibFailed] = useState(false);
  const [reusedBaseline, setReusedBaseline] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const reachedRef = useRef<string | null>(null);

  const onSecond = useCallback(
    (item: FaceBatchItem) => {
      batchRef.current.push(item);
      if (batchRef.current.length >= BATCH_SIZE) flush();
    },
    [flush],
  );
  const onCalibrated = useCallback(
    (frames: FrameMeasure[], blinks: number, ms: number) => {
      const b = patientId ? buildBaseline(patientId, frames, blinks, ms) : null;
      if (!b) {
        setCalibFailed(true);
        setCalibAttempt((n) => n + 1);
        return;
      }
      setCalibFailed(false);
      saveBaseline(b);
      setReusedBaseline(false);
      setExIdx(0);
      setStep("exercise");
    },
    [patientId, saveBaseline],
  );

  const tracker = useFaceTracker({ palsy, baseline, onSecond, onCalibrated });
  const { engine, snap, status, error } = tracker;

  // Camera running → calibrate, or reuse a baseline younger than 7 days.
  useEffect(() => {
    if (status !== "running" || step !== "camera") return;
    if (baseline) {
      setReusedBaseline(true);
      setExIdx(0);
      setStep("exercise");
    } else {
      setStep("calibrate");
    }
  }, [status, step, baseline]);

  // Warm the TTS cache for every spoken instruction while the camera/model are still loading.
  useEffect(() => {
    warmInstructions([
      t("face.calib.speak"),
      ...EXERCISE_ORDER.map((key) => t(`face.exercise.${key}` as I18nKey)),
      t("face.reached", { n: REPS_TARGET }),
      t("face.summary.title"),
    ]);
  }, []);

  // Calibration window (10 s of measured frames).
  useEffect(() => {
    if (step !== "calibrate" || status !== "running") return;
    engine.startCalibration(CALIBRATION_MS);
    speak(t("face.calib.speak"));
    return () => engine.cancelCalibration();
  }, [step, status, engine, calibAttempt]);

  // Exercise entry: rep counter + voice instruction.
  useEffect(() => {
    if (step !== "exercise") return;
    const key = EXERCISE_ORDER[exIdx];
    engine.setExercise(key);
    reachedRef.current = null;
    speak(t(`face.exercise.${key}` as I18nKey));
    return () => engine.setExercise(null);
  }, [step, exIdx, engine]);

  useEffect(() => () => stopSpeaking(), []);

  const reps = snap.rep.reps;
  const reached = step === "exercise" && reps >= REPS_TARGET;
  useEffect(() => {
    if (!reached) return;
    const key = `${exIdx}`;
    if (reachedRef.current === key) return;
    reachedRef.current = key;
    speak(t("face.reached", { n: REPS_TARGET }));
  }, [reached, exIdx]);

  function finishExercise() {
    const key = EXERCISE_ORDER[exIdx];
    const stats = engine.exerciseStats();
    const meanAmp = stats.rep.amplitudes.length ? mean(stats.rep.amplitudes) : 0;
    const { score, result } = exerciseScore(stats.rep.reps, REPS_TARGET, meanAmp, stats.fsi);
    const w = weakerSide(stats.sides);
    const card: ExerciseResultCard = {
      key,
      reps: stats.rep.reps,
      target: REPS_TARGET,
      meanAmp,
      fsi: stats.fsi,
      score,
      result,
      weakerSide: w.side,
      sideAsym: w.asym,
    };
    setResults((r) => [...r, card]);
    if (exIdx + 1 < EXERCISE_ORDER.length) {
      setExIdx(exIdx + 1);
    } else {
      setStep("summary");
      tracker.stop();
      flush();
      speak(t("face.summary.title"));
    }
  }

  function restart() {
    setResults([]);
    setExIdx(0);
    setStep("camera");
    if (videoRef.current) void tracker.start(videoRef.current);
  }

  function recalibrate() {
    clearBaseline();
    setReusedBaseline(false);
    setResults([]);
    setExIdx(0);
    setCalibFailed(false);
    setStep(status === "running" ? "calibrate" : "camera");
  }

  if (!patientId && pidPending) return <LoadingCard />;

  const frame = snap.frame;
  const faceState: "ok" | "no_face" | "turn" = !frame?.present
    ? "no_face"
    : frame.inRange
      ? "ok"
      : "turn";
  const fsiNow = frame?.measured ? frame.fsi : null;
  const showVideo = step !== "summary";
  const exKey = EXERCISE_ORDER[exIdx];

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-[1.3em] font-bold">
          <ScanFace aria-hidden className="text-primary size-[1em] shrink-0" />
          {t("face.title")}
        </h1>
        {step === "exercise" && (
          <span className="bg-muted ring-border inline-flex items-center rounded-full px-3 py-0.5 text-[0.8em] font-semibold ring-1 ring-inset">
            {t("face.step", { index: exIdx + 1, total: EXERCISE_ORDER.length })}
          </span>
        )}
      </div>
      <div className={cn("relative", !showVideo && "hidden")}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="shadow-soft aspect-[4/3] w-full -scale-x-100 rounded-2xl bg-black object-cover"
        />
        {status === "running" && (
          <div
            role="status"
            aria-live="polite"
            className={cn(
              "absolute top-3 left-3 flex items-center gap-2 rounded-full px-4 py-2 font-medium",
              faceState === "ok" ? "bg-green-50 text-green-950" : "bg-amber-100 text-amber-950",
            )}
          >
            {faceState === "ok" ? (
              <ScanFace aria-hidden className="size-[1.2em]" />
            ) : (
              <TriangleAlert aria-hidden className="size-[1.2em]" />
            )}
            {t(`face.status.${faceState}` as I18nKey)}
          </div>
        )}
        <div className="bg-background/90 text-foreground absolute right-3 bottom-3 flex items-center gap-2 rounded-full px-3 py-1 text-[0.8em]">
          <ShieldCheck aria-hidden className="size-[1.2em]" />
          {t("face.privacy")}
        </div>
      </div>

      {sessionError ? (
        <p className="text-muted-foreground text-[0.85em]">{t("face.session.offline")}</p>
      ) : null}

      {step === "camera" && (
        <div className="flex flex-col gap-4">
          <p>{t("face.intro")}</p>
          {error && (
            <div
              role="alert"
              className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-amber-950"
            >
              <CameraOff aria-hidden className="mt-1 size-[1.4em] shrink-0" />
              <span>{t(`face.error.${error}` as I18nKey)}</span>
            </div>
          )}
          {status === "idle" || status === "error" ? (
            <BigButton
              icon={<Camera aria-hidden className="size-[2em]" />}
              label={error ? t("common.retry") : t("face.camera.start")}
              onClick={() => {
                if (videoRef.current) void tracker.start(videoRef.current);
              }}
            />
          ) : (
            <LoadingCard
              text={status === "camera" ? t("face.camera.starting") : t("face.model.loading")}
            />
          )}
          <Link
            href="/p/exercise"
            className={cn(buttonVariants({ variant: "outline" }), "min-h-16 text-[1em]")}
          >
            {t("face.back")}
          </Link>
        </div>
      )}

      {step === "calibrate" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-[1.3em]">{t("face.calib.title")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p>{t("face.calib.text", { sec: Math.round(CALIBRATION_MS / 1000) })}</p>
            {calibFailed && (
              <div
                role="alert"
                className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-amber-950"
              >
                <TriangleAlert aria-hidden className="mt-1 size-[1.4em] shrink-0" />
                <span>{t("face.calib.failed")}</span>
              </div>
            )}
            <ProgressBar
              label={t("face.calib.progress")}
              value={snap.calibProgress ?? 0}
              text={`${Math.round(((snap.calibProgress ?? 0) * CALIBRATION_MS) / 1000)} / ${Math.round(CALIBRATION_MS / 1000)} s`}
            />
          </CardContent>
        </Card>
      )}

      {step === "exercise" && (
        <div className="flex flex-col gap-4">
          {reusedBaseline && baseline && (
            <p className="text-muted-foreground text-[0.8em]">
              {t("face.calib.reused", { days: baselineAgeDays(baseline) })}
            </p>
          )}

          <div className="bg-card shadow-soft flex flex-col items-center gap-2 rounded-2xl border px-5 py-5 text-center">
            <HoldRing
              progress={Math.min(1, snap.rep.holdMs / HOLD_TARGET_MS)}
              emoji={EMOJI[exKey]}
            />
            <p className="text-[28px] leading-snug font-semibold">
              {t(`face.exercise.${exKey}` as I18nKey)}
            </p>
            <p className="text-muted-foreground" aria-live="polite">
              {snap.rep.holdMs >= HOLD_TARGET_MS
                ? t("face.release")
                : snap.rep.signal >= REP_ON
                  ? t("face.hold")
                  : t("face.hold_hint")}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Stat
              label={t("face.symmetry")}
              value={pct(fsiNow)}
              sub={
                baseline && fsiNow !== null
                  ? `${t("face.base")} ${pct(baseline.fsiBase)} · ${signed(fsiNow - baseline.fsiBase)}`
                  : undefined
              }
            />
            <Stat label={t("face.reps")} value={`${reps} / ${REPS_TARGET}`} />
          </div>
          <ProgressBar
            label={t("face.amplitude")}
            value={snap.rep.signal}
            text={`${Math.round(snap.rep.signal * 100)} %`}
            marker={REP_ON}
          />

          {reached && (
            <ResultBanner result="correct" text={t("face.reached", { n: REPS_TARGET })} />
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <Button
              variant="outline"
              className="min-h-16 gap-2 text-[1em]"
              onClick={finishExercise}
              disabled={reached}
            >
              <SkipForward aria-hidden className="size-6" />
              {t("exercise.skip")}
            </Button>
            <Button
              className="min-h-16 gap-2 text-[1em]"
              onClick={finishExercise}
              disabled={!reached}
            >
              {t("exercise.next")}
              <ArrowRight aria-hidden className="size-6" />
            </Button>
          </div>
          <Button variant="ghost" className="min-h-16 gap-2 text-[1em]" onClick={recalibrate}>
            <RotateCw aria-hidden className="size-6" />
            {t("face.calib.redo")}
          </Button>
        </div>
      )}

      {step === "summary" && (
        <Summary
          results={results}
          baseFsi={baseline?.fsiBase ?? null}
          onAgain={restart}
          onRecalibrate={recalibrate}
        />
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-card shadow-soft flex flex-col rounded-2xl border px-4 py-3">
      <span className="text-muted-foreground text-[0.85em]">{label}</span>
      <span className="text-primary-deep text-[2em] leading-tight font-bold tabular-nums">
        {value}
      </span>
      {sub && <span className="text-muted-foreground text-[0.85em]">{sub}</span>}
    </div>
  );
}

function ProgressBar({
  label,
  value,
  text,
  marker,
}: {
  label: string;
  value: number;
  text: string;
  marker?: number;
}) {
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between">
        <span>{label}</span>
        <span className="font-semibold">{text}</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(v * 100)}
        className="bg-muted relative h-6 w-full overflow-hidden rounded-full border"
      >
        <div className="bg-primary h-full rounded-full" style={{ width: `${v * 100}%` }} />
        {marker !== undefined && (
          <div
            aria-hidden
            className="bg-foreground absolute top-0 h-full w-1"
            style={{ left: `${marker * 100}%` }}
          />
        )}
      </div>
    </div>
  );
}

// Hold progress ring (3 s target) around the animated-emoji instruction.
function HoldRing({ progress, emoji }: { progress: number; emoji: string }) {
  const r = 70;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative size-[170px]">
      <svg viewBox="0 0 160 160" className="size-full -rotate-90" aria-hidden>
        <circle cx="80" cy="80" r={r} fill="none" strokeWidth="10" className="stroke-muted" />
        <circle
          cx="80"
          cy="80"
          r={r}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - progress)}
          className="stroke-primary"
        />
      </svg>
      <span
        aria-hidden
        className="absolute inset-0 flex items-center justify-center text-[96px] leading-none"
      >
        {emoji}
      </span>
    </div>
  );
}

function Summary({
  results,
  baseFsi,
  onAgain,
  onRecalibrate,
}: {
  results: ExerciseResultCard[];
  baseFsi: number | null;
  onAgain: () => void;
  onRecalibrate: () => void;
}) {
  const fsis = results.map((r) => r.fsi).filter((v): v is number => v !== null);
  const best = fsis.length ? Math.max(...fsis) : null;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-[1.3em]">
            <span className="inline-flex size-[2em] shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-700">
              <Trophy aria-hidden className="size-[1.1em]" />
            </span>
            {t("face.summary.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p>
            {t("face.summary.best_fsi")}: <strong>{pct(best)}</strong>
            {best !== null && baseFsi !== null && (
              <span className="text-muted-foreground">
                {" "}
                ({t("face.base")} {pct(baseFsi)}, {signed(best - baseFsi)}{" "}
                {t("face.summary.vs_base")})
              </span>
            )}
          </p>
        </CardContent>
      </Card>

      {results.map((card) => (
        <Card key={card.key}>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-[1.2em]">
              <span aria-hidden className="text-[1.6em] leading-none">
                {EMOJI[card.key]}
              </span>
              {t(`face.name.${card.key}` as I18nKey)}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <ResultBanner result={card.result} text={feedbackText(card)} />
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
              <span className="text-muted-foreground">{t("face.reps")}</span>
              <strong>
                {card.reps} / {card.target}
              </strong>
              <span className="text-muted-foreground">{t("face.amplitude")}</span>
              <strong>{pct(card.meanAmp)}</strong>
              <span className="text-muted-foreground">{t("face.symmetry")}</span>
              <strong>{pct(card.fsi)}</strong>
              <span className="text-muted-foreground">{t("face.summary.score")}</span>
              <strong>{pct(card.score)}</strong>
            </div>
          </CardContent>
        </Card>
      ))}

      <div className="grid gap-3 sm:grid-cols-2">
        <Button className="min-h-16 gap-2 text-[1em]" onClick={onAgain}>
          <RotateCw aria-hidden className="size-6" />
          {t("face.again")}
        </Button>
        <Button variant="outline" className="min-h-16 gap-2 text-[1em]" onClick={onRecalibrate}>
          {t("face.calib.redo")}
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/p/exercise"
          className={cn(buttonVariants({ variant: "outline" }), "min-h-16 text-[1em]")}
        >
          {t("face.back")}
        </Link>
        <Link
          href="/p"
          className={cn(buttonVariants({ variant: "outline" }), "min-h-16 text-[1em]")}
        >
          {t("nav.patient_home")}
        </Link>
      </div>
    </div>
  );
}
