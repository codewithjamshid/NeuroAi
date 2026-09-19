"use client";

import { CircleDashed, Inbox, RotateCw, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { errorMessage } from "@/lib/api";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

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
    <Card className={cn("border-destructive/40", className)}>
      <CardContent className="flex flex-wrap items-center gap-3">
        <TriangleAlert aria-hidden className="text-destructive size-[1.4em] shrink-0" />
        <span className="flex-1">{errorMessage(error)}</span>
        {onRetry && (
          <Button variant="outline" onClick={onRetry} className="gap-1.5">
            <RotateCw aria-hidden />
            {t("common.retry")}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function LoadingCard({ text, className }: { text?: string; className?: string }) {
  return (
    <div className={cn("text-muted-foreground flex items-center gap-2 py-4", className)}>
      <CircleDashed aria-hidden className="size-[1.2em] animate-spin" />
      {text ?? t("common.loading")}
    </div>
  );
}

export function EmptyState({ text, className }: { text?: string; className?: string }) {
  return (
    <div className={cn("text-muted-foreground flex items-center gap-2 py-4", className)}>
      <Inbox aria-hidden className="size-[1.2em]" />
      {text ?? t("common.empty")}
    </div>
  );
}
