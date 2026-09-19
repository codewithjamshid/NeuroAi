import { Activity, BatteryLow, Brain, HeartPulse, Smile } from "lucide-react";

import type { PatientState } from "@/features/sessions/types";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

// "AI shunday tushundi" (TZ §8.1): simplified PatientState — 4 compact pills, icon + text, plus
// the plain-words explanation list.
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
      className={cn("bg-muted/60 flex flex-col gap-2 rounded-2xl px-4 py-3", className)}
    >
      <p className="text-muted-foreground flex items-center gap-1.5 text-[0.8em] font-semibold tracking-wide uppercase">
        <Brain aria-hidden className="size-[1.1em]" />
        {t("state.title")}
      </p>
      <ul className="flex flex-wrap gap-2">
        {items.map(({ Icon, label, value }) => (
          <li
            key={label}
            className="bg-card ring-border inline-flex items-center gap-1.5 rounded-full px-3 py-1 ring-1 ring-inset"
          >
            <Icon aria-hidden className="text-primary size-[1em]" />
            <span className="text-muted-foreground">{label}:</span>
            <span className="font-semibold">{value}</span>
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
