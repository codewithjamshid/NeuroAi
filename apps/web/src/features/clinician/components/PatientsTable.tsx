"use client";

import { Flag, UserPlus } from "lucide-react";
import Link from "next/link";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useClinicianPatients } from "../hooks";

export function PatientsTable() {
  const q = useClinicianPatients();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{t("d.patients.title")}</h1>
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
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-left">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">{t("patient.full_name")}</th>
                <th className="px-3 py-2 font-medium">{t("patient.age")}</th>
                <th className="px-3 py-2 font-medium">{t("patient.aphasia_type")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.flags")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.last_activity")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.adherence")}</th>
              </tr>
            </thead>
            <tbody>
              {q.data.map((p) => (
                <tr key={p.id} className="hover:bg-muted/50 border-t">
                  <td className="px-3 py-2">
                    <Link
                      href={`/d/patients/${p.id}`}
                      className="text-primary font-medium underline-offset-2 hover:underline"
                    >
                      {p.full_name}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{p.age ?? "—"}</td>
                  <td className="px-3 py-2">{p.aphasia_type ?? "—"}</td>
                  <td className="px-3 py-2">
                    {p.open_flags > 0 ? (
                      <Badge variant="destructive" className="gap-1">
                        <Flag aria-hidden />
                        {p.open_flags}
                      </Badge>
                    ) : (
                      <Badge variant="outline">0</Badge>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {p.last_activity ? new Date(p.last_activity).toLocaleString() : "—"}
                  </td>
                  <td className="px-3 py-2">
                    {p.adherence_week === null || p.adherence_week === undefined
                      ? "—"
                      : `${Math.round(p.adherence_week <= 1 ? p.adherence_week * 100 : p.adherence_week)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
