"use client";

import { useMutation } from "@tanstack/react-query";
import { Send, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { CandidateCards } from "@/components/CandidateCards";
import { ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { MicButton } from "@/components/MicButton";
import { RichText } from "@/components/RichText";
import { StatusPill } from "@/components/StatusPill";
import { Button, buttonVariants } from "@/components/ui/button";
import { MicErrorNotice } from "@/features/audio/components/MicErrorNotice";
import { useAudioStore } from "@/features/audio/store";
import { useAudioPlayer } from "@/features/audio/useAudioPlayer";
import { useRecorder } from "@/features/audio/useRecorder";
import { usePatientId } from "@/features/patients/hooks";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { confirmCandidate, type MessageInput, sendMessage } from "../api";
import { useSessionLifecycle } from "../hooks";
import type { MessageResponse } from "../types";
import { StatePanel } from "./StatePanel";

// TZ §4.8 one voice turn: tap → record (VAD) → POST messages → text + TTS + candidates + state.
export function TalkScreen() {
  const { patientId, isPending: pidPending } = usePatientId();
  const { session, error: sessionError, retry } = useSessionLifecycle(patientId, "companion");
  const recorder = useRecorder();
  const player = useAudioPlayer();
  const status = useAudioStore((s) => s.status);
  const setStatus = useAudioStore((s) => s.setStatus);
  const [reply, setReply] = useState<MessageResponse | null>(null);
  const [text, setText] = useState("");
  const [turnError, setTurnError] = useState<unknown>(null);

  const sendM = useMutation({
    mutationFn: (input: MessageInput) => sendMessage(session?.id as string, input),
  });
  const confirmM = useMutation({
    mutationFn: (key: string) => confirmCandidate(session?.id as string, key),
  });

  async function handleResponse(res: MessageResponse) {
    setReply(res);
    await player.play(res.ai_message.tts_url, res.ai_message.text);
  }

  async function runTurn(input: MessageInput, viaConfirm?: string) {
    if (!session) return;
    setTurnError(null);
    setStatus("thinking");
    try {
      const res = viaConfirm
        ? await confirmM.mutateAsync(viaConfirm)
        : await sendM.mutateAsync(input);
      await handleResponse(res);
    } catch (e) {
      setTurnError(e);
      setStatus("idle");
    }
  }

  async function onMic() {
    if (recorder.state === "listening") {
      recorder.stop();
      return;
    }
    if (!session) return;
    player.stop();
    const blob = await recorder.start();
    if (!blob) {
      setStatus("idle");
      return;
    }
    await runTurn({ audio: blob });
  }

  const busy =
    status === "thinking" || status === "speaking" || sendM.isPending || confirmM.isPending;
  const risk = reply?.risk;

  return (
    <div className="flex flex-1 flex-col gap-4">
      {reply?.state && <StatePanel state={reply.state} />}

      {sessionError ? (
        <ErrorCard error={sessionError} onRetry={retry} />
      ) : !session && (pidPending || patientId) ? (
        <LoadingCard text={t("talk.starting")} />
      ) : !patientId ? (
        <ErrorCard error={new Error(t("p.no_patient"))} />
      ) : null}

      {risk && risk.level === "high" && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-2xl border-2 border-red-700 bg-red-50 px-4 py-3 text-red-950"
        >
          <ShieldAlert aria-hidden className="mt-1 size-[1.4em] shrink-0" />
          <span>{t("talk.risk_high")}</span>
        </div>
      )}

      <section aria-live="polite" className="flex-1">
        {reply?.patient_message?.text && (
          <p className="text-muted-foreground mb-2 text-[0.85em]">
            {t("talk.you")}: {reply.patient_message.text}
          </p>
        )}
        <RichText
          text={reply?.ai_message.text ?? t("talk.intro")}
          className="text-[28px] leading-snug font-medium"
        />
      </section>

      {reply?.needs_confirmation && reply.candidates.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="font-medium">{t("talk.confirm_prompt")}</p>
          <CandidateCards
            candidates={reply.candidates}
            disabled={busy}
            onSelect={(key) => void runTurn({ pictogram_key: key }, key)}
            onOther={() => void runTurn({ text: t("talk.other_text") })}
          />
        </div>
      )}

      {reply?.suggested_action === "start_exercise" && (
        <Link href="/p/exercise" className={cn(buttonVariants({ variant: "outline" }), "min-h-16")}>
          {t("talk.go_exercise")}
        </Link>
      )}

      {turnError ? <ErrorCard error={turnError} /> : null}
      <MicErrorNotice error={recorder.error} />

      <div className="flex flex-col items-center gap-3 py-2">
        <StatusPill status={status} />
        <MicButton
          status={status}
          level={recorder.level}
          onPress={() => void onMic()}
          disabled={!session}
        />
      </div>

      <form
        className="flex gap-2"
        onSubmit={(ev) => {
          ev.preventDefault();
          const v = text.trim();
          if (!v || busy) return;
          setText("");
          void runTurn({ text: v });
        }}
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("talk.text_placeholder")}
          aria-label={t("talk.text_placeholder")}
          disabled={!session || busy}
          className="border-input bg-background min-h-16 flex-1 rounded-xl border-2 px-4"
        />
        <Button type="submit" disabled={!session || busy} className="min-h-16 gap-2 px-5">
          <Send aria-hidden className="size-6" />
          {t("common.send")}
        </Button>
      </form>
    </div>
  );
}
