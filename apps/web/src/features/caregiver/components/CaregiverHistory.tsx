"use client";

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

// /c/history — daily summaries (stub: session list with caregiver_text).
export function CaregiverHistory() {
  const { patientId, isPending: pidPending } = usePatientId();
  const sessions = usePatientSessions(patientId, 20);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">{t("c.history.title")}</h1>
      {!patientId && !pidPending ? (
        <EmptyState text={t("p.no_patient")} />
      ) : sessions.isPending ? (
        <LoadingCard />
      ) : sessions.isError ? (
        <ErrorCard error={sessions.error} onRetry={() => sessions.refetch()} />
      ) : sessions.data.length === 0 ? (
        <EmptyState />
      ) : (
        <ul className="flex flex-col gap-2">
          {sessions.data.map((s) => (
            <li key={s.id} className="rounded-lg border px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <Badge variant="secondary">{tk(`session.mode.${s.mode}`)}</Badge>
                <span className="text-muted-foreground text-xs">
                  {new Date(s.started_at).toLocaleString()}
                </span>
              </div>
              <p className="mt-1 text-sm">{summaryText(s.summary) ?? t("c.history.no_summary")}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
