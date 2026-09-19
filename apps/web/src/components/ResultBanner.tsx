import { CircleCheck, CircleMinus, RotateCcw, SkipForward } from "lucide-react";

import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type ExerciseResult = "correct" | "partial" | "incorrect" | "skipped";

// Result feedback with icon + text (TZ §8.1: never color alone): ✓ To'g'ri / ≈ Deyarli / ↻ Yana.
// Status colors are reserved (dataviz status palette) and always paired with an icon.
const meta: Record<ExerciseResult, { Icon: typeof CircleCheck; cls: string; icon: string }> = {
  correct: {
    Icon: CircleCheck,
    cls: "bg-green-50 text-green-950 border-green-300",
    icon: "bg-green-100 text-green-800",
  },
  partial: {
    Icon: CircleMinus,
    cls: "bg-amber-50 text-amber-950 border-amber-300",
    icon: "bg-amber-100 text-amber-800",
  },
  incorrect: {
    Icon: RotateCcw,
    cls: "bg-red-50 text-red-950 border-red-300",
    icon: "bg-red-100 text-red-800",
  },
  skipped: {
    Icon: SkipForward,
    cls: "bg-muted text-foreground border-border",
    icon: "bg-card text-muted-foreground",
  },
};

export function ResultBanner({
  result,
  text,
  className,
}: {
  result: ExerciseResult;
  text?: string;
  className?: string;
}) {
  const { Icon, cls, icon } = meta[result];
  return (
    <div
      role="status"
      aria-live="assertive"
      className={cn("flex items-center gap-3 rounded-2xl border px-4 py-3", cls, className)}
    >
      <span
        className={cn(
          "inline-flex size-[2.4em] shrink-0 items-center justify-center rounded-full",
          icon,
        )}
      >
        <Icon aria-hidden className="size-[1.5em]" />
      </span>
      <div className="flex min-w-0 flex-col">
        <span className="text-[1.2em] leading-tight font-bold">
          {t(`exercise.result.${result}`)}
        </span>
        {text && <span className="leading-snug">{text}</span>}
      </div>
    </div>
  );
}
