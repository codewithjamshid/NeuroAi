"use client";

import { LayoutGrid, MessageSquareText, RotateCcw, Users } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { CandidateCards } from "@/components/CandidateCards";
import { ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { MicButton } from "@/components/MicButton";
import { StatusPill } from "@/components/StatusPill";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MicErrorNotice } from "@/features/audio/components/MicErrorNotice";
import { useAudioStore } from "@/features/audio/store";
import { useAudioPlayer } from "@/features/audio/useAudioPlayer";
import { useRecorder } from "@/features/audio/useRecorder";
import { useInterpretations, usePatientId } from "@/features/patients/hooks";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useConfirm, useGuess } from "../hooks";
import type { ConfirmResponse, GuessResponse } from "../types";

export function SpokenResult({
  spoken_text,
  family_note,
  compact,
}: {
  spoken_text: string;
  family_note?: string | null;
  compact?: boolean;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div
        className={cn(
          "rounded-2xl border-2 border-teal-700 bg-teal-50 px-5 py-4 text-teal-950 dark:bg-teal-950 dark:text-teal-50",
          compact ? "text-[1.3em]" : "text-[1.8em] leading-snug",
        )}
      >
        <MessageSquareText aria-hidden className="mb-1 size-[1em]" />
        <p className="font-bold">{spoken_text}</p>
      </div>
      {family_note && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users aria-hidden className="size-[1.2em]" />
              {t("say.family_note")}
            </CardTitle>
          </CardHeader>
          <CardContent>{family_note}</CardContent>
        </Card>
      )}
    </div>
  );
}

// /p/say (patient) and /c/say (mirror=true: polls the latest interpretation every 2 s).
export function SayScreen({
  mirror = false,
  boardHref = "/p/board",
}: {
  mirror?: boolean;
  boardHref?: string;
}) {
  const router = useRouter();
  const { patientId, isPending: pidPending } = usePatientId();
  const recorder = useRecorder();
  const player = useAudioPlayer();
  const status = useAudioStore((s) => s.status);
  const setStatus = useAudioStore((s) => s.setStatus);
  const guessM = useGuess(patientId);
  const confirmM = useConfirm(patientId);
  const [guess, setGuess] = useState<GuessResponse | null>(null);
  const [result, setResult] = useState<ConfirmResponse | null>(null);
  const latest = useInterpretations(patientId, 1, mirror ? 2000 : undefined);

  function reset() {
    setGuess(null);
    setResult(null);
    guessM.reset();
    confirmM.reset();
    player.stop();
  }

  async function onMic() {
    if (recorder.state === "listening") {
      recorder.stop();
      return;
    }
    reset();
    const blob = await recorder.start();
    if (!blob) {
      setStatus("idle");
      return;
    }
    setStatus("thinking");
    try {
      const g = await guessM.mutateAsync({ audio: blob });
      setGuess(g);
      if (g.candidates.length === 0 && g.board_suggested) {
        router.push(`${boardHref}?iid=${encodeURIComponent(g.interpretation_id)}`);
        return;
      }
      setStatus("idle");
    } catch {
      setStatus("idle");
    }
  }

  async function onPick(key: string) {
    if (!guess) return;
    setStatus("thinking");
    try {
      const r = await confirmM.mutateAsync({
        interpretation_id: guess.interpretation_id,
        candidate_key: key,
      });
      setResult(r);
      await player.play(r.tts_url, r.spoken_text);
    } catch {
      setStatus("idle");
    }
  }

  const busy = status !== "idle" || guessM.isPending || confirmM.isPending;
  const mirrored = mirror ? latest.data?.[0] : undefined;

  if (!patientId && !pidPending) return <ErrorCard error={new Error(t("p.no_patient"))} />;

  return (
    <div className="flex flex-1 flex-col gap-4">
      {mirror && (
        <Card>
          <CardHeader>
            <CardTitle className="text-[1.1em]">{t("c.say.latest")}</CardTitle>
          </CardHeader>
          <CardContent>
            {latest.isPending ? (
              <LoadingCard />
            ) : latest.isError ? (
              <ErrorCard error={latest.error} onRetry={() => latest.refetch()} />
            ) : mirrored?.spoken_text ? (
              <SpokenResult
                spoken_text={mirrored.spoken_text}
                family_note={mirrored.family_note}
                compact
              />
            ) : (
              <p className="text-muted-foreground">{t("c.say.none")}</p>
            )}
          </CardContent>
        </Card>
      )}

      {result ? (
        <>
          <SpokenResult spoken_text={result.spoken_text} family_note={result.family_note} />
          {result.follow_up === "body_map" && (
            <Link
              href={boardHref}
              className={cn(buttonVariants({ variant: "outline" }), "min-h-16 text-[1em]")}
            >
              {t("say.body_map_hint")}
            </Link>
          )}
          <Button variant="outline" className="min-h-16 gap-2 text-[1em]" onClick={reset}>
            <RotateCcw aria-hidden className="size-6" />
            {t("say.again")}
          </Button>
        </>
      ) : guess ? (
        <div className="flex flex-col gap-2">
          {guess.raw_transcript && (
            <p className="text-muted-foreground text-[0.85em]">
              {t("say.heard")}: {guess.raw_transcript}
            </p>
          )}
          <p className="text-[1.2em] font-medium">{t("say.pick")}</p>
          <CandidateCards
            candidates={guess.candidates}
            disabled={busy}
            onSelect={(key) => void onPick(key)}
            onOther={() =>
              router.push(`${boardHref}?iid=${encodeURIComponent(guess.interpretation_id)}`)
            }
          />
        </div>
      ) : (
        <p className="text-[1.3em] font-medium">{mirror ? t("c.say.intro") : t("say.intro")}</p>
      )}

      {guessM.isError && <ErrorCard error={guessM.error} />}
      {confirmM.isError && <ErrorCard error={confirmM.error} />}
      <MicErrorNotice error={recorder.error} />

      <div className="flex flex-col items-center gap-3 py-2">
        <StatusPill status={status} />
        <MicButton
          status={status}
          level={recorder.level}
          onPress={() => void onMic()}
          disabled={!patientId}
        />
      </div>

      <Link
        href={boardHref}
        className={cn(buttonVariants({ variant: "outline" }), "min-h-16 gap-2 text-[1em]")}
      >
        <LayoutGrid aria-hidden className="size-6" />
        {t("say.board")}
      </Link>
    </div>
  );
}
