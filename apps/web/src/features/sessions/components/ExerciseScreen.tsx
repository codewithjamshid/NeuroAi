"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Ear, Lightbulb, SkipForward, Trophy } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { MicButton } from "@/components/MicButton";
import { ResultBanner } from "@/components/ResultBanner";
import { StatusPill } from "@/components/StatusPill";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MicErrorNotice } from "@/features/audio/components/MicErrorNotice";
import { useAudioStore } from "@/features/audio/store";
import { useAudioPlayer } from "@/features/audio/useAudioPlayer";
import { useRecorder } from "@/features/audio/useRecorder";
import { usePatientId } from "@/features/patients/hooks";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { getNextExercise, skipAttempt, submitAttempt } from "../api";
import { useSessionLifecycle } from "../hooks";
import type { NextExercise, SubmitResult } from "../types";

function pct(v: number | undefined | null): string {
  return v === undefined || v === null ? "—" : `${Math.round(v * 100)}%`;
}

const chipCls =
  "bg-muted text-foreground ring-border inline-flex items-center rounded-full px-3 py-0.5 text-[0.8em] font-semibold ring-1 ring-inset";

// TZ §8.2 /p/exercise: stimulus, prompt, mic, result animation (icon + text), cue, progress, skip.
export function ExerciseScreen() {
  const { patientId, isPending: pidPending } = usePatientId();
  const { session, error: sessionError, retry } = useSessionLifecycle(patientId, "exercise");
  const recorder = useRecorder();
  const player = useAudioPlayer();
  const status = useAudioStore((s) => s.status);
  const setStatus = useAudioStore((s) => s.setStatus);
  const [current, setCurrent] = useState<NextExercise | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [text, setText] = useState("");
  const loadedFor = useRef<string | null>(null);

  const nextM = useMutation({
    mutationFn: () => getNextExercise(session?.id as string),
    onSuccess: (data) => {
      setResult(null);
      setCurrent(data);
      if (!data.done) void player.play(data.template.prompt_tts_url, data.template.prompt_text);
    },
  });
  const submitM = useMutation({
    mutationFn: (input: { audio: Blob } | { text: string }) =>
      submitAttempt((current && !current.done ? current.attempt_id : "") as string, input),
    onSuccess: async (res) => {
      setResult(res);
      await player.play(res.tts_url, res.feedback_text);
      if (res.next_cue) await player.play(res.next_cue.tts_url, res.next_cue.text);
    },
    onError: () => setStatus("idle"),
  });
  const skipM = useMutation({
    mutationFn: () => skipAttempt((current && !current.done ? current.attempt_id : "") as string),
    onSuccess: () => nextM.mutate(),
  });

  useEffect(() => {
    if (session && loadedFor.current !== session.id) {
      loadedFor.current = session.id;
      nextM.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  async function onMic() {
    if (recorder.state === "listening") {
      recorder.stop();
      return;
    }
    player.stop();
    const blob = await recorder.start();
    if (!blob) {
      setStatus("idle");
      return;
    }
    setStatus("thinking");
    submitM.mutate({ audio: blob });
  }

  const busy = status !== "idle" || submitM.isPending || nextM.isPending || skipM.isPending;

  if (sessionError) return <ErrorCard error={sessionError} onRetry={retry} />;
  if (!patientId && !pidPending) return <ErrorCard error={new Error(t("p.no_patient"))} />;
  if (!session || (!current && nextM.isPending))
    return <LoadingCard text={t("exercise.loading")} />;
  if (nextM.isError && !current)
    return <ErrorCard error={nextM.error} onRetry={() => nextM.mutate()} />;
  if (!current) return <LoadingCard text={t("exercise.loading")} />;

  if (current.done) {
    const stats = [
      { label: t("exercise.done.accuracy"), value: pct(current.summary.accuracy) },
      { label: t("exercise.done.independence"), value: pct(current.summary.independence) },
      { label: t("exercise.done.attempts"), value: String(current.summary.attempts ?? "—") },
    ];
    return (
      <Card className="mx-auto w-full max-w-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-[1.3em]">
            <span className="inline-flex size-[2em] shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-700">
              <Trophy aria-hidden className="size-[1.1em]" />
            </span>
            {t("exercise.done.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-3 sm:grid-cols-3">
            {stats.map(({ label, value }) => (
              <div key={label} className="bg-muted/60 flex flex-col rounded-2xl px-4 py-3">
                <span className="text-muted-foreground text-[0.8em]">{label}</span>
                <span className="text-[1.6em] leading-tight font-bold">{value}</span>
              </div>
            ))}
          </div>
          <Link href="/p" className={cn(buttonVariants({ size: "lg" }), "min-h-16 text-[1em]")}>
            {t("nav.patient_home")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  const { template, progress, cue_level } = current;
  const canAdvance = result?.next_action === "next_item" || result?.next_action === "suggest_break";
  const ratio = progress.total > 0 ? Math.min(1, progress.index / progress.total) : 0;
  const stim = template.stimulus;
  const bigText = !stim?.image && !stim?.emoji && stim?.text;

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-semibold">
            {t("exercise.progress", { index: progress.index, total: progress.total })}
          </span>
          <div className="flex flex-wrap gap-2">
            <span className={chipCls}>{t("exercise.level_chip", { level: template.level })}</span>
            <span className={chipCls}>
              {t("exercise.cue_chip", { level: result?.next_cue?.level ?? cue_level })}
            </span>
          </div>
        </div>
        <div
          role="progressbar"
          aria-label={t("exercise.progress_label")}
          aria-valuemin={0}
          aria-valuemax={progress.total}
          aria-valuenow={progress.index}
          className="bg-muted h-3 w-full overflow-hidden rounded-full"
        >
          <div className="bg-primary h-full rounded-full" style={{ width: `${ratio * 100}%` }} />
        </div>
      </div>

      <div className="bg-card shadow-soft flex flex-col items-center gap-3 rounded-2xl border px-5 py-6 text-center">
        {stim?.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={stim.image} alt="" className="max-h-56 rounded-xl" />
        ) : bigText ? (
          <span className="text-primary-deep text-[2.2em] leading-tight font-bold">
            {stim?.text}
          </span>
        ) : (
          <span aria-hidden className="text-[96px] leading-none">
            {stim?.emoji ?? "❓"}
          </span>
        )}
        {!bigText && stim?.text && (
          <span className="text-[1.6em] leading-tight font-bold">{stim.text}</span>
        )}
        <p className="text-[28px] leading-snug font-medium">{template.prompt_text}</p>
      </div>

      {result && (
        <div className="flex flex-col gap-2">
          <ResultBanner result={result.result} text={result.feedback_text} />
          {result.recognized_text && (
            <p className="text-muted-foreground flex items-center gap-2 px-1 text-[0.85em]">
              <Ear aria-hidden className="size-[1em] shrink-0" />
              {t("exercise.heard")}: {result.recognized_text}
            </p>
          )}
          {result.next_cue && (
            <div className="flex items-start gap-3 rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sky-950">
              <Lightbulb aria-hidden className="mt-1 size-[1.4em] shrink-0 text-sky-700" />
              <span className="flex flex-col gap-1">
                <span className="inline-flex self-start rounded-full bg-sky-100 px-2.5 py-0.5 text-[0.8em] font-semibold text-sky-900">
                  {t("exercise.cue_label", { level: result.next_cue.level })}
                </span>
                <span>{result.next_cue.text}</span>
              </span>
            </div>
          )}
        </div>
      )}

      {submitM.isError && <ErrorCard error={submitM.error} />}
      {skipM.isError && <ErrorCard error={skipM.error} />}
      {nextM.isError && <ErrorCard error={nextM.error} onRetry={() => nextM.mutate()} />}
      <MicErrorNotice error={recorder.error} />

      <div className="flex flex-col items-center gap-4 py-2">
        <StatusPill status={status} />
        <MicButton status={status} level={recorder.level} onPress={() => void onMic()} />
      </div>

      <form
        className="flex gap-2"
        onSubmit={(ev) => {
          ev.preventDefault();
          const v = text.trim();
          if (!v || busy) return;
          setText("");
          setStatus("thinking");
          submitM.mutate({ text: v });
        }}
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("exercise.text_placeholder")}
          aria-label={t("exercise.text_placeholder")}
          disabled={busy}
          className="field min-h-16 flex-1 rounded-2xl px-4"
        />
        <Button type="submit" variant="outline" disabled={busy} className="min-h-16 px-5">
          {t("common.send")}
        </Button>
      </form>

      <div className="grid gap-3 sm:grid-cols-2">
        <Button
          variant="outline"
          className="min-h-16 gap-2 text-[1em]"
          disabled={busy}
          onClick={() => skipM.mutate()}
        >
          <SkipForward aria-hidden className="size-6" />
          {t("exercise.skip")}
        </Button>
        <Button
          className="min-h-16 gap-2 text-[1em]"
          disabled={!canAdvance || nextM.isPending}
          onClick={() => nextM.mutate()}
        >
          {t("exercise.next")}
          <ArrowRight aria-hidden className="size-6" />
        </Button>
      </div>
    </div>
  );
}
