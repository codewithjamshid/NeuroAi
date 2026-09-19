"use client";

import { CircleDashed, Mic, Square } from "lucide-react";

import type { AudioStatus } from "@/features/audio/types";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

// Central mic (TZ §8.1, ≥ 96px → 112px). Tap = start; tap while listening = stop early.
// While listening a soft ring pulses outwards (hidden under prefers-reduced-motion) and the
// level-driven halo grows with the voice.
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
    <span className="relative inline-flex">
      {listening && (
        <span
          aria-hidden
          data-motion
          className="animate-mic-pulse absolute inset-0 rounded-full bg-red-600/35 motion-reduce:hidden"
        />
      )}
      <button
        type="button"
        onClick={onPress}
        disabled={disabled || busy}
        aria-label={label}
        aria-pressed={listening}
        className={cn(
          "focus-visible:ring-ring relative flex size-28 items-center justify-center rounded-full text-white outline-none focus-visible:ring-4 focus-visible:ring-offset-4 active:translate-y-px disabled:opacity-60",
          listening ? "bg-red-700" : "bg-primary hover:bg-primary-hover shadow-lift",
          className,
        )}
        style={
          listening
            ? { boxShadow: `0 0 0 ${Math.round(6 + level * 24)}px rgba(185,28,28,0.22)` }
            : undefined
        }
      >
        {listening ? (
          <Square aria-hidden className="size-11" />
        ) : busy ? (
          <CircleDashed aria-hidden data-motion className="size-12 animate-spin" />
        ) : (
          <Mic aria-hidden className="size-14" />
        )}
      </button>
    </span>
  );
}
