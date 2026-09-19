"use client";

import { Phone } from "lucide-react";

import { env } from "@/lib/env";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores";

// TZ §8.1: always visible on patient screens; follows the one-hand setting.
// Amber = the one accent colour, reserved for CTAs; icon + text so it never relies on colour.
// Caregiver phone comes with T-15; until then it dials the emergency number.
export function HelpButton() {
  const hand = useUiStore((s) => s.hand);

  return (
    <a
      href={`tel:${env.emergencyNumber}`}
      className={cn(
        "bg-highlight text-highlight-foreground shadow-lift hover:bg-highlight-hover focus-visible:ring-ring fixed bottom-4 z-50 inline-flex min-h-16 items-center gap-3 rounded-full px-6 text-2xl font-semibold ring-4 ring-white/80 outline-none focus-visible:ring-4 active:translate-y-px",
        hand === "left" ? "left-4" : "right-4",
      )}
    >
      <Phone aria-hidden className="size-7" />
      {t("help")}
    </a>
  );
}
