"use client";

import { CircleCheck, CircleDashed, WifiOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useHealth } from "../hooks";

// Icon + text (TZ §3: never rely on color alone).
export function HealthBadge({ className }: { className?: string }) {
  const { data, isError, isPending } = useHealth();

  if (isPending) {
    return (
      <Badge variant="outline" className={cn("gap-1.5", className)}>
        <CircleDashed aria-hidden className="animate-spin" />
        {t("health.checking")}
      </Badge>
    );
  }

  if (isError || data?.status !== "ok") {
    return (
      <Badge variant="destructive" className={cn("gap-1.5", className)}>
        <WifiOff aria-hidden />
        {t("health.offline")}
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className={cn("gap-1.5 border-teal-700 text-teal-800 dark:text-teal-300", className)}
    >
      <CircleCheck aria-hidden />
      {t("health.ok")}
    </Badge>
  );
}
