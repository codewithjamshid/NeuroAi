import { CircleCheck, CircleMinus, CircleX, SkipForward } from "lucide-react";

import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type ExerciseResult = "correct" | "partial" | "incorrect" | "skipped";

// Result feedback with icon + text (TZ §8.1: never color alone). Status colors are reserved
// (dataviz status palette: good / warning / critical) and always paired with an icon.
const meta: Record<ExerciseResult, { Icon: typeof CircleCheck; cls: string }> = {
  correct: { Icon: CircleCheck, cls: "bg-green-50 text-green-950 border-green-700" },
  partial: { Icon: CircleMinus, cls: "bg-amber-50 text-amber-950 border-amber-600" },
  incorrect: { Icon: CircleX, cls: "bg-red-50 text-red-950 border-red-700" },
  skipped: { Icon: SkipForward, cls: "bg-muted text-foreground border-border" },
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
  const { Icon, cls } = meta[result];
  return (
    <div
      role="status"
      aria-live="assertive"
      className={cn("flex items-center gap-3 rounded-2xl border-2 px-4 py-3", cls, className)}
    >
      <Icon aria-hidden className="size-[2em] shrink-0" />
      <div className="flex flex-col">
        <span className="text-[1.2em] font-bold">{t(`exercise.result.${result}`)}</span>
        {text && <span>{text}</span>}
      </div>
    </div>
  );
}
