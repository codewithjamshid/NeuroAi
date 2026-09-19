"use client";

import { CircleDashed, Mic, Square } from "lucide-react";

import type { AudioStatus } from "@/features/audio/types";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

// Central mic (TZ §8.1, ≥ 96px). Tap = start; tap while listening = stop early.
export function MicButton({
  status,
  level = 0,
  onPress,
  disabled,
  className,
}: {
  status: AudioStatus;
  level?: number;
  onPress: () => void;
  disabled?: boolean;
  className?: string;
}) {
  const listening = status === "listening";
  const busy = status === "thinking" || status === "speaking";
  const label = listening ? t("audio.mic.stop") : busy ? t("audio.mic.wait") : t("audio.mic.start");
  return (
    <button
      type="button"
      onClick={onPress}
      disabled={disabled || busy}
      aria-label={label}
      aria-pressed={listening}
      className={cn(
        "focus-visible:ring-ring relative flex size-36 items-center justify-center rounded-full text-white shadow-lg outline-none focus-visible:ring-4 disabled:opacity-60",
        listening ? "bg-red-700" : "bg-primary",
        className,
      )}
      style={
        listening
          ? { boxShadow: `0 0 0 ${Math.round(6 + level * 24)}px rgba(185,28,28,0.25)` }
          : undefined
      }
    >
      {listening ? (
        <Square aria-hidden className="size-14" />
      ) : busy ? (
        <CircleDashed aria-hidden className="size-14 animate-spin" />
      ) : (
        <Mic aria-hidden className="size-16" />
      )}
    </button>
  );
}
