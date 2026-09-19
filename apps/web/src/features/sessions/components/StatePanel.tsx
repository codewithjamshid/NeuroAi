import { Activity, BatteryLow, HeartPulse, Smile } from "lucide-react";

import type { PatientState } from "@/features/sessions/types";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

// "AI shunday tushundi" (TZ §8.1): simplified PatientState — plain words, icon + text.
export function StatePanel({ state, className }: { state: PatientState; className?: string }) {
  const items = [
    {
      Icon: Activity,
      label: t("state.engagement"),
      value: t(`state.engagement.${state.engagement}`),
    },
    { Icon: BatteryLow, label: t("state.fatigue"), value: `${Math.round(state.fatigue * 100)}%` },
    { Icon: Smile, label: t("state.mood"), value: t(`state.mood.${state.mood}`) },
    {
      Icon: HeartPulse,
      label: t("state.distress"),
      value: state.distress ? t("common.yes") : t("common.no"),
    },
  ];
  return (
    <section
      aria-label={t("state.title")}
      className={cn("bg-muted/60 flex flex-col gap-1 rounded-xl px-3 py-2", className)}
    >
      <ul className="flex flex-wrap gap-x-4 gap-y-1">
        {items.map(({ Icon, label, value }) => (
          <li key={label} className="flex items-center gap-1.5">
            <Icon aria-hidden className="size-[1em]" />
            <span className="text-muted-foreground">{label}:</span>
            <span className="font-medium">{value}</span>
          </li>
        ))}
      </ul>
      {state.explain && state.explain.length > 0 && (
        <ul className="text-muted-foreground list-disc pl-6 text-[0.85em]">
          {state.explain.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
