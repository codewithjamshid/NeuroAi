"use client";

import { Brain, Ear, Mic, Volume2 } from "lucide-react";

import type { AudioStatus } from "@/features/audio/types";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const meta: Record<AudioStatus, { Icon: typeof Mic; cls: string }> = {
  idle: { Icon: Mic, cls: "bg-muted text-foreground ring-border" },
  listening: { Icon: Ear, cls: "bg-sky-50 text-sky-950 ring-sky-200" },
  thinking: { Icon: Brain, cls: "bg-amber-50 text-amber-950 ring-amber-200" },
  speaking: { Icon: Volume2, cls: "bg-teal-50 text-teal-950 ring-teal-200" },
};

// Voice-turn status (TZ §8.1): "Eshityapman… / O'ylayapman… / Gapiryapman…" — icon + text.
export function StatusPill({ status, className }: { status: AudioStatus; className?: string }) {
  const { Icon, cls } = meta[status];
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-4 py-2 font-semibold ring-1 ring-inset",
        cls,
        className,
      )}
    >
      <Icon aria-hidden className="size-[1.2em]" />
      {t(`audio.status.${status}`)}
    </div>
  );
}
