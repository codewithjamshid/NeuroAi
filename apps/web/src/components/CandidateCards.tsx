"use client";

import { LayoutGrid } from "lucide-react";

import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type CandidateLike = { key: string; label: string; emoji?: string | null; p?: number };

// 3 big cards (emoji + label) + optional "Boshqa" → board (TZ §8.2 /p/say, /p/talk).
export function CandidateCards({
  candidates,
  onSelect,
  onOther,
  disabled,
  className,
}: {
  candidates: CandidateLike[];
  onSelect: (key: string) => void;
  onOther?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("grid gap-3 sm:grid-cols-3", className)}>
      {candidates.map((c) => (
        <button
          key={c.key}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(c.key)}
          className="bg-card shadow-soft hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-36 flex-col items-center justify-center gap-2 rounded-2xl border-2 px-3 py-4 text-center text-[1.2em] font-semibold outline-none focus-visible:ring-4 active:translate-y-px disabled:opacity-50"
        >
          <span aria-hidden className="text-[2.4em] leading-none">
            {c.emoji ?? "💬"}
          </span>
          <span className="leading-tight">{c.label}</span>
        </button>
      ))}
      {onOther && (
        <button
          type="button"
          disabled={disabled}
          onClick={onOther}
          className="bg-muted/60 text-foreground hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-36 flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-3 py-4 text-center text-[1.2em] font-semibold outline-none focus-visible:ring-4 disabled:opacity-50"
        >
          <LayoutGrid aria-hidden className="size-[2em]" />
          <span>{t("say.other")}</span>
        </button>
      )}
    </div>
  );
}
