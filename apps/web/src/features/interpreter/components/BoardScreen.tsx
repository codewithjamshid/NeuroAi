"use client";

import { RotateCcw } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Pictogram } from "@/components/Pictogram";
import { Button, buttonVariants } from "@/components/ui/button";
import { useAudioPlayer } from "@/features/audio/useAudioPlayer";
import { usePatientId } from "@/features/patients/hooks";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useBoard, useConfirm, useGuess } from "../hooks";
import type { BoardItem, BodyZone, ConfirmResponse } from "../types";
import { SpokenResult } from "./SayScreen";

// TZ §7.7 body map fallback when the API sends none.
const DEFAULT_BODY: BodyZone[] = [
  { key: "pain:head", label: "Bosh", emoji: "🧠" },
  { key: "pain:chest", label: "Ko'krak", emoji: "🫀" },
  { key: "pain:stomach", label: "Qorin", emoji: "🫃" },
  { key: "pain:arm", label: "Qo'l", emoji: "💪" },
  { key: "pain:leg", label: "Oyoq", emoji: "🦵" },
  { key: "pain:back", label: "Orqa", emoji: "🔙" },
];

export function BoardScreen({ backHref = "/p/say" }: { backHref?: string }) {
  const params = useSearchParams();
  const iid = params.get("iid");
  const { patientId, isPending: pidPending } = usePatientId();
  const board = useBoard(patientId);
  const guessM = useGuess(patientId);
  const confirmM = useConfirm(patientId);
  const player = useAudioPlayer();
  const [result, setResult] = useState<ConfirmResponse | null>(null);
  const [picked, setPicked] = useState<string | null>(null);

  const groups = useMemo(() => {
    const map = new Map<string, BoardItem[]>();
    for (const item of board.data?.items ?? []) {
      const g = item.group ?? "other";
      if (!map.has(g)) map.set(g, []);
      map.get(g)?.push(item);
    }
    return [...map.entries()];
  }, [board.data]);

  const busy = guessM.isPending || confirmM.isPending;

  async function pick(key: string, label: string) {
    if (busy) return;
    setPicked(key);
    try {
      let interpretationId = iid;
      if (!interpretationId) {
        const g = await guessM.mutateAsync({ text: label });
        interpretationId = g.interpretation_id;
      }
      const r = await confirmM.mutateAsync({
        interpretation_id: interpretationId,
        candidate_key: key,
        custom_text: label,
      });
      setResult(r);
      await player.play(r.tts_url, r.spoken_text);
    } catch {
      /* surfaced via mutation error state */
    }
  }

  if (!patientId && !pidPending) return <ErrorCard error={new Error(t("p.no_patient"))} />;

  if (result) {
    return (
      <div className="flex flex-col gap-4">
        <SpokenResult spoken_text={result.spoken_text} family_note={result.family_note} />
        <Button
          variant="outline"
          className="min-h-16 gap-2 text-[1em]"
          onClick={() => {
            setResult(null);
            setPicked(null);
            player.stop();
          }}
        >
          <RotateCcw aria-hidden className="size-6" />
          {t("say.again")}
        </Button>
        <Link
          href={backHref}
          className={cn(buttonVariants({ variant: "ghost" }), "min-h-16 text-[1em]")}
        >
          {t("board.back")}
        </Link>
      </div>
    );
  }

  const bodyMap = board.data?.body_map?.length ? board.data.body_map : DEFAULT_BODY;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-[1.4em] font-bold">{t("board.title")}</h1>
        <Link
          href={backHref}
          className={cn(buttonVariants({ variant: "outline" }), "min-h-16 text-[1em]")}
        >
          {t("board.back")}
        </Link>
      </div>

      {guessM.isError && <ErrorCard error={guessM.error} />}
      {confirmM.isError && <ErrorCard error={confirmM.error} />}

      {board.isPending ? (
        <LoadingCard />
      ) : board.isError ? (
        <ErrorCard error={board.error} onRetry={() => board.refetch()} />
      ) : groups.length === 0 ? (
        <EmptyState />
      ) : (
        groups.map(([group, items]) => (
          <section key={group} className="flex flex-col gap-2">
            <h2 className="text-muted-foreground text-[0.9em] font-semibold uppercase">
              {tk(`board.group.${group}`)}
            </h2>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
              {items.map((item) => (
                <Pictogram
                  key={item.key}
                  emoji={item.emoji}
                  label={item.label}
                  selected={picked === item.key}
                  disabled={busy}
                  onClick={() => void pick(item.key, item.label)}
                />
              ))}
            </div>
          </section>
        ))
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-muted-foreground text-[0.9em] font-semibold uppercase">
          {t("board.body_map")}
        </h2>
        <div className="grid grid-cols-3 gap-2">
          {bodyMap.map((z) => (
            <Pictogram
              key={z.key}
              emoji={z.emoji ?? "🤕"}
              label={z.label}
              selected={picked === z.key}
              disabled={busy || !patientId}
              onClick={() => void pick(z.key, `${z.label} ${t("board.pain_suffix")}`)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
