"use client";

import { Flag, UserPlus, Users } from "lucide-react";
import Link from "next/link";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useClinicianPatients } from "../hooks";

const th =
  "bg-muted text-muted-foreground sticky top-0 z-10 px-3 py-2 text-xs font-semibold uppercase tracking-wide";

function adherencePct(v: number | null | undefined): number | null {
  if (v === null || v === undefined) return null;
  return Math.round(v <= 1 ? v * 100 : v);
}

export function PatientsTable() {
  const q = useClinicianPatients();

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h1 className="flex items-center gap-2 text-2xl">
            <Users aria-hidden className="text-primary size-6" />
            {t("d.patients.title")}
          </h1>
          <p className="text-muted-foreground">{t("d.patients.subtitle")}</p>
        </div>
        <Link href="/d/patients/new" className={cn(buttonVariants(), "gap-1.5")}>
          <UserPlus aria-hidden />
          {t("d.patients.new")}
        </Link>
      </div>

      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState text={t("d.patients.empty")} />
      ) : (
        <div className="bg-card shadow-soft max-h-[70vh] overflow-auto rounded-xl border">
          <table className="w-full text-left">
            <thead>
              <tr>
                <th className={th}>{t("patient.full_name")}</th>
                <th className={th}>{t("patient.age")}</th>
                <th className={th}>{t("patient.aphasia_type")}</th>
                <th className={th}>{t("d.col.flags")}</th>
                <th className={th}>{t("d.col.last_activity")}</th>
                <th className={th}>{t("d.col.adherence")}</th>
              </tr>
            </thead>
            <tbody>
              {q.data.map((p) => {
                const adh = adherencePct(p.adherence_week);
                return (
                  <tr
                    key={p.id}
                    className="odd:bg-card even:bg-muted/40 hover:bg-accent/60 border-t transition-colors"
                  >
                    <td className="px-3 py-2.5">
                      <Link
                        href={`/d/patients/${p.id}`}
                        className="text-primary-deep font-medium underline-offset-2 hover:underline"
                      >
                        {p.full_name}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5">{p.age ?? "—"}</td>
                    <td className="px-3 py-2.5">
                      {p.aphasia_type ? tk(`aphasia.${p.aphasia_type}`) : "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      {p.open_flags > 0 ? (
                        <Badge variant="destructive" className="gap-1">
                          <Flag aria-hidden />
                          {p.open_flags}
                        </Badge>
                      ) : (
                        <Badge variant="outline">0</Badge>
                      )}
                    </td>
                    <td className="px-3 py-2.5 whitespace-nowrap">
                      {p.last_activity ? new Date(p.last_activity).toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      {adh === null ? (
                        "—"
                      ) : (
                        <span className="inline-flex items-center gap-2">
                          <span
                            aria-hidden
                            className="bg-muted inline-block h-1.5 w-16 overflow-hidden rounded-full"
                          >
                            <span
                              className="bg-primary block h-full rounded-full"
                              style={{ width: `${Math.min(100, adh)}%` }}
                            />
                          </span>
                          <span className="tabular-nums">{adh}%</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
