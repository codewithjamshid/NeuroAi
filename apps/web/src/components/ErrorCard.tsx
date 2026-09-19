"use client";

import { CircleDashed, Inbox, RotateCw, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { errorMessage } from "@/lib/api";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

// Error / loading / empty states share one shape: rounded box, icon + text, optional action.
export function ErrorCard({
  error,
  onRetry,
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "border-destructive/30 text-foreground flex flex-wrap items-center gap-3 rounded-xl border bg-red-50/70 px-4 py-3",
        className,
      )}
    >
      <TriangleAlert aria-hidden className="text-destructive size-[1.4em] shrink-0" />
      <span className="min-w-0 flex-1">{errorMessage(error)}</span>
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="bg-card gap-1.5">
          <RotateCw aria-hidden />
          {t("common.retry")}
        </Button>
      )}
    </div>
  );
}

export function LoadingCard({ text, className }: { text?: string; className?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "text-muted-foreground bg-muted/60 flex items-center gap-3 rounded-xl px-4 py-3",
        className,
      )}
    >
      <CircleDashed aria-hidden data-motion className="text-primary size-[1.2em] animate-spin" />
      {text ?? t("common.loading")}
    </div>
  );
}

export function EmptyState({ text, className }: { text?: string; className?: string }) {
  return (
    <div
      className={cn(
        "text-muted-foreground flex items-center gap-3 rounded-xl border border-dashed px-4 py-3",
        className,
      )}
    >
      <span className="bg-muted inline-flex size-9 shrink-0 items-center justify-center rounded-full">
        <Inbox aria-hidden className="size-[1.2em]" />
      </span>
      {text ?? t("common.empty")}
    </div>
  );
}
