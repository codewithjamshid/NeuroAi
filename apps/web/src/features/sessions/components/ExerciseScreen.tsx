"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Lightbulb, SkipForward, Trophy } from "lucide-react";
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
    return (
      <Card className="mx-auto w-full max-w-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.3em]">
            <Trophy aria-hidden className="size-[1.3em]" />
            {t("exercise.done.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p>
            {t("exercise.done.accuracy")}: <strong>{pct(current.summary.accuracy)}</strong>
          </p>
          <p>
            {t("exercise.done.independence")}: <strong>{pct(current.summary.independence)}</strong>
          </p>
          <p>
            {t("exercise.done.attempts")}: <strong>{current.summary.attempts ?? "—"}</strong>
          </p>
          <Link href="/p" className={cn(buttonVariants({ size: "lg" }), "min-h-16 text-[1em]")}>
            {t("nav.patient_home")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  const { template, progress, cue_level } = current;
  const canAdvance = result?.next_action === "next_item" || result?.next_action === "suggest_break";

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground">
          {t("exercise.progress", { index: progress.index, total: progress.total })}
        </span>
        <span className="text-muted-foreground">
          {t("exercise.level")}: {template.level} · {t("exercise.cue")}:{" "}
          {result?.next_cue?.level ?? cue_level}
        </span>
      </div>

      <div className="flex flex-col items-center gap-3 py-2 text-center">
        {template.stimulus?.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={template.stimulus.image} alt="" className="max-h-56 rounded-xl" />
        ) : (
          <span aria-hidden className="text-[120px] leading-none">
            {template.stimulus?.emoji ?? "❓"}
          </span>
        )}
        {template.stimulus?.text && (
          <span className="text-[1.6em] font-bold">{template.stimulus.text}</span>
        )}
        <p className="text-[28px] leading-snug font-medium">{template.prompt_text}</p>
      </div>

      {result && (
        <div className="flex flex-col gap-2">
          <ResultBanner result={result.result} text={result.feedback_text} />
          {result.recognized_text && (
            <p className="text-muted-foreground text-[0.85em]">
              {t("exercise.heard")}: {result.recognized_text}
            </p>
          )}
          {result.next_cue && (
            <div className="flex items-start gap-3 rounded-2xl border-2 border-sky-700 bg-sky-50 px-4 py-3 text-sky-950">
              <Lightbulb aria-hidden className="mt-1 size-[1.4em] shrink-0" />
              <span>
                <strong>{t("exercise.cue_label", { level: result.next_cue.level })}:</strong>{" "}
                {result.next_cue.text}
              </span>
            </div>
          )}
        </div>
      )}

      {submitM.isError && <ErrorCard error={submitM.error} />}
      {skipM.isError && <ErrorCard error={skipM.error} />}
      {nextM.isError && <ErrorCard error={nextM.error} onRetry={() => nextM.mutate()} />}
      <MicErrorNotice error={recorder.error} />

      <div className="flex flex-col items-center gap-3 py-2">
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
          className="border-input bg-background min-h-16 flex-1 rounded-xl border-2 px-4"
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
