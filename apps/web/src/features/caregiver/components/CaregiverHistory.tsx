"use client";

import { History } from "lucide-react";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { usePatientSessions } from "@/features/clinician/hooks";
import { usePatientId } from "@/features/patients/hooks";
import { t, tk } from "@/lib/i18n";

function summaryText(s: unknown): string | null {
  if (!s) return null;
  if (typeof s === "string") return s;
  if (typeof s === "object" && "caregiver_text" in s) {
    return String((s as { caregiver_text?: string }).caregiver_text ?? "");
  }
  return null;
}

// /c/history — daily summaries (stub: session list with caregiver_text) as a timeline.
export function CaregiverHistory() {
  const { patientId, isPending: pidPending } = usePatientId();
  const sessions = usePatientSessions(patientId, 20);

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-0.5">
        <h1 className="flex items-center gap-2 text-2xl">
          <History aria-hidden className="text-primary size-6" />
          {t("c.history.title")}
        </h1>
        <p className="text-muted-foreground text-sm">{t("c.history.hint")}</p>
      </header>
      {!patientId && !pidPending ? (
        <EmptyState text={t("p.no_patient")} />
      ) : sessions.isPending ? (
        <LoadingCard />
      ) : sessions.isError ? (
        <ErrorCard error={sessions.error} onRetry={() => sessions.refetch()} />
      ) : sessions.data.length === 0 ? (
        <EmptyState />
      ) : (
        <ol className="border-border ml-2 flex flex-col gap-4 border-l-2 pl-5">
          {sessions.data.map((s) => (
            <li key={s.id} className="relative">
              <span
                aria-hidden
                className="bg-primary ring-background absolute top-2 -left-[27px] size-3 rounded-full ring-4"
              />
              <div className="bg-card shadow-soft flex flex-col gap-1.5 rounded-xl border px-4 py-3">
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="secondary">{tk(`session.mode.${s.mode}`)}</Badge>
                  <span className="text-muted-foreground text-xs">
                    {new Date(s.started_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm leading-snug">
                  {summaryText(s.summary) ?? (
                    <span className="text-muted-foreground">{t("c.history.no_summary")}</span>
                  )}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
