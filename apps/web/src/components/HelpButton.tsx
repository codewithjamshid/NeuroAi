"use client";

import { Phone } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { env } from "@/lib/env";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores";

// TZ §8.1: always visible on patient screens; follows the one-hand setting.
// Caregiver phone comes with T-15; until then it dials the emergency number.
export function HelpButton() {
  const hand = useUiStore((s) => s.hand);

  return (
    <a
      href={`tel:${env.emergencyNumber}`}
      className={cn(
        buttonVariants({ size: "lg" }),
        "fixed bottom-4 z-50 min-h-16 gap-3 rounded-full px-6 text-2xl font-semibold shadow-lg",
        hand === "left" ? "left-4" : "right-4",
      )}
    >
      <Phone aria-hidden className="size-7" />
      {t("help")}
    </a>
  );
}
