"use client";

import { FileText, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import Markdown from "react-markdown";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useDashboard,
  usePatient,
  useRedFlagMutation,
  useRedFlags,
} from "@/features/patients/hooks";
import type { RedFlagStatus } from "@/features/patients/types";
import { useTranscript } from "@/features/sessions/hooks";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import {
  useCreateMedication,
  useCreateProtocol,
  useGenerateReport,
  useMedications,
  usePatientSessions,
  useProtocol,
  useProtocolTemplates,
  useReports,
} from "../hooks";
import { DashboardCharts } from "./DashboardCharts";

const TABS = ["overview", "sessions", "flags", "protocol", "medications", "report"] as const;
type Tab = (typeof TABS)[number];
const FLAG_STATUSES: RedFlagStatus[] = ["open", "acknowledged", "resolved"];
const inputCls = "border-input bg-background min-h-9 rounded-md border px-2";

export function PatientDetail({ patientId }: { patientId: string }) {
  const [tab, setTab] = useState<Tab>("overview");
  const patient = usePatient(patientId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href="/d" className="text-muted-foreground text-xs hover:underline">
            ← {t("d.patients.title")}
          </Link>
          <h1 className="text-2xl font-semibold">
            {patient.data?.full_name ?? (patient.isError ? t("d.patient.unknown") : "…")}
          </h1>
          {patient.data && (
            <p className="text-muted-foreground">
              {patient.data.birth_year ?? "—"} · {patient.data.aphasia_type ?? "—"} ·{" "}
              {patient.data.dialect ?? "—"}
            </p>
          )}
        </div>
      </div>
      {patient.isError && <ErrorCard error={patient.error} onRetry={() => patient.refetch()} />}

      <nav role="tablist" className="flex flex-wrap gap-1 border-b">
        {TABS.map((k) => (
          <button
            key={k}
            role="tab"
            type="button"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={cn(
              "-mb-px rounded-t-md border-b-2 px-3 py-2 font-medium",
              tab === k
                ? "border-primary text-primary"
                : "text-muted-foreground hover:text-foreground border-transparent",
            )}
          >
            {t(`d.tab.${k}`)}
          </button>
        ))}
      </nav>

      {tab === "overview" && <OverviewTab patientId={patientId} />}
      {tab === "sessions" && <SessionsTab patientId={patientId} />}
      {tab === "flags" && <FlagsTab patientId={patientId} />}
      {tab === "protocol" && <ProtocolTab patientId={patientId} />}
      {tab === "medications" && <MedicationsTab patientId={patientId} />}
      {tab === "report" && <ReportTab patientId={patientId} />}
    </div>
  );
}

function OverviewTab({ patientId }: { patientId: string }) {
  const q = useDashboard(patientId);
  if (q.isPending) return <LoadingCard />;
  if (q.isError) return <ErrorCard error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data.days?.length) return <EmptyState text={t("d.dashboard.empty")} />;
  return <DashboardCharts data={q.data} />;
}

function summaryOf(s: unknown): string {
  if (!s) return "";
  if (typeof s === "string") return s;
  const o = s as { clinician_text?: string; caregiver_text?: string };
  return o.clinician_text ?? o.caregiver_text ?? "";
}

function SessionsTab({ patientId }: { patientId: string }) {
  const q = usePatientSessions(patientId, 30);
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="relative">
      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-left">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">{t("d.col.started")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.mode")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.accuracy")}</th>
                <th className="px-3 py-2 font-medium">{t("d.col.summary")}</th>
              </tr>
            </thead>
            <tbody>
              {q.data.map((s) => (
                <tr
                  key={s.id}
                  className="hover:bg-muted/50 cursor-pointer border-t"
                  onClick={() => setOpen(s.id)}
                >
                  <td className="px-3 py-2 whitespace-nowrap">
                    {new Date(s.started_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    <Badge variant="secondary">{tk(`session.mode.${s.mode}`)}</Badge>
                  </td>
                  <td className="px-3 py-2">
                    {s.accuracy === null || s.accuracy === undefined
                      ? "—"
                      : `${Math.round(s.accuracy * 100)}%`}
                  </td>
                  <td className="text-muted-foreground max-w-md truncate px-3 py-2">
                    {summaryOf(s.summary) || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && <TranscriptDrawer sessionId={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

function TranscriptDrawer({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const q = useTranscript(sessionId);
  return (
    <aside
      role="dialog"
      aria-label={t("d.transcript.title")}
      className="bg-background fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col gap-3 overflow-y-auto border-l p-4 shadow-xl"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("d.transcript.title")}</h2>
        <Button variant="ghost" size="icon" aria-label={t("common.close")} onClick={onClose}>
          <X aria-hidden />
        </Button>
      </div>
      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : (
        <>
          {summaryOf(q.data.session.summary) && (
            <p className="bg-muted rounded-md p-2">{summaryOf(q.data.session.summary)}</p>
          )}
          <ul className="flex flex-col gap-2">
            {q.data.messages.map((m) => (
              <li
                key={m.id}
                className={cn(
                  "max-w-[90%] rounded-lg px-3 py-2",
                  m.role === "patient"
                    ? "self-end bg-teal-50 dark:bg-teal-950"
                    : "bg-muted self-start",
                )}
              >
                <p className="text-muted-foreground text-xs">
                  {tk(`role.${m.role}`)} · {m.modality}
                  {typeof m.stt_confidence === "number"
                    ? ` · ${Math.round(m.stt_confidence * 100)}%`
                    : ""}
                </p>
                <p>{m.text}</p>
              </li>
            ))}
            {q.data.messages.length === 0 && <EmptyState />}
          </ul>
        </>
      )}
    </aside>
  );
}

function FlagsTab({ patientId }: { patientId: string }) {
  const q = useRedFlags(patientId);
  const m = useRedFlagMutation(patientId);
  if (q.isPending) return <LoadingCard />;
  if (q.isError) return <ErrorCard error={q.error} onRetry={() => q.refetch()} />;
  if (q.data.length === 0) return <EmptyState text={t("d.flags.empty")} />;
  return (
    <div className="flex flex-col gap-2">
      {m.isError && <ErrorCard error={m.error} />}
      {q.data.map((f) => (
        <Card key={f.id} size="sm">
          <CardContent className="flex flex-wrap items-center gap-3">
            <Badge
              variant={
                f.severity === "high"
                  ? "destructive"
                  : f.severity === "medium"
                    ? "secondary"
                    : "outline"
              }
            >
              {tk(`flag.severity.${f.severity}`)}
            </Badge>
            <span className="font-medium">{tk(`flag.category.${f.category}`)}</span>
            <span className="text-muted-foreground flex-1">{f.evidence ?? "—"}</span>
            <span className="text-muted-foreground text-xs">
              {new Date(f.created_at).toLocaleString()}
            </span>
            <select
              aria-label={t("d.flags.status")}
              className={inputCls}
              value={f.status}
              disabled={m.isPending}
              onChange={(e) => m.mutate({ id: f.id, status: e.target.value as RedFlagStatus })}
            >
              {FLAG_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {t(`flag.status.${s}`)}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ProtocolTab({ patientId }: { patientId: string }) {
  const q = useProtocol(patientId);
  const templates = useProtocolTemplates();
  const create = useCreateProtocol(patientId);
  const [key, setKey] = useState("");
  const options = templates.data ?? [];
  const selected = key || options[0]?.key || "";
  return (
    <div className="flex flex-col gap-4">
      <Card size="sm">
        <CardContent className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1">
            <span className="font-medium">{t("d.protocol.template")}</span>
            <select
              className={inputCls}
              value={selected}
              onChange={(e) => setKey(e.target.value)}
              disabled={options.length === 0}
            >
              {options.map((tpl) => (
                <option key={tpl.key} value={tpl.key}>
                  {tpl.title}
                </option>
              ))}
            </select>
          </label>
          <Button
            disabled={!selected || create.isPending}
            onClick={() => create.mutate({ template_key: selected })}
            className="min-h-9"
          >
            {t("d.protocol.create")}
          </Button>
          {templates.isError && (
            <ErrorCard
              error={templates.error}
              onRetry={() => templates.refetch()}
              className="w-full"
            />
          )}
          {create.isError && <ErrorCard error={create.error} className="w-full" />}
        </CardContent>
      </Card>

      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : !q.data ? (
        <EmptyState text={t("d.protocol.none")} />
      ) : (
        <Card size="sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {q.data.title}
              <Badge variant="outline">{tk(`protocol.status.${q.data.status}`)}</Badge>
              {q.data.start_date && (
                <span className="text-muted-foreground text-xs">{q.data.start_date}</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="py-1 pr-3 font-medium">{t("d.protocol.kind")}</th>
                  <th className="py-1 pr-3 font-medium">{t("d.protocol.category")}</th>
                  <th className="py-1 pr-3 font-medium">{t("exercise.level")}</th>
                  <th className="py-1 pr-3 font-medium">{t("d.protocol.frequency")}</th>
                  <th className="py-1 pr-3 font-medium">{t("d.protocol.duration")}</th>
                </tr>
              </thead>
              <tbody>
                {q.data.items.map((it) => (
                  <tr key={it.id} className="border-t">
                    <td className="py-1 pr-3">{tk(`protocol.kind.${it.kind}`)}</td>
                    <td className="py-1 pr-3">
                      {it.category ? tk(`exercise.category.${it.category}`) : "—"}
                    </td>
                    <td className="py-1 pr-3">{it.level ?? "—"}</td>
                    <td className="py-1 pr-3">
                      {it.frequency
                        ? `${String((it.frequency as { times_per_day?: unknown }).times_per_day ?? "")} ${t("d.protocol.per_day")}`
                        : "—"}
                    </td>
                    <td className="py-1 pr-3">
                      {it.duration_min ? `${it.duration_min} ${t("common.min")}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MedicationsTab({ patientId }: { patientId: string }) {
  const q = useMedications(patientId);
  const create = useCreateMedication(patientId);
  const [f, setF] = useState({ name: "", dose: "", times: "09:00" });
  return (
    <div className="flex flex-col gap-4">
      <Card size="sm">
        <CardContent>
          <form
            className="flex flex-wrap items-end gap-2"
            onSubmit={(ev) => {
              ev.preventDefault();
              create.mutate(
                {
                  name: f.name.trim(),
                  dose: f.dose.trim() || undefined,
                  schedule: {
                    times: f.times
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  },
                },
                { onSuccess: () => setF({ name: "", dose: "", times: "09:00" }) },
              );
            }}
          >
            <label className="flex flex-col gap-1">
              <span className="font-medium">{t("d.med.name")}</span>
              <input
                required
                className={inputCls}
                value={f.name}
                onChange={(e) => setF({ ...f, name: e.target.value })}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="font-medium">{t("d.med.dose")}</span>
              <input
                className={inputCls}
                value={f.dose}
                onChange={(e) => setF({ ...f, dose: e.target.value })}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="font-medium">{t("d.med.times")}</span>
              <input
                className={inputCls}
                value={f.times}
                onChange={(e) => setF({ ...f, times: e.target.value })}
              />
            </label>
            <Button type="submit" disabled={create.isPending} className="min-h-9">
              {t("d.med.add")}
            </Button>
          </form>
          {create.isError && <ErrorCard error={create.error} className="mt-2" />}
        </CardContent>
      </Card>
      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState text={t("d.med.empty")} />
      ) : (
        <ul className="flex flex-col gap-2">
          {q.data.map((m) => (
            <li
              key={m.id}
              className="flex flex-wrap items-center gap-3 rounded-lg border px-3 py-2"
            >
              <span className="font-medium">{m.name}</span>
              <span className="text-muted-foreground">{m.dose ?? ""}</span>
              <span className="text-muted-foreground text-xs">
                {Array.isArray((m.schedule as { times?: unknown })?.times)
                  ? ((m.schedule as { times: string[] }).times ?? []).join(", ")
                  : ""}
              </span>
              {m.active === false && <Badge variant="outline">{t("d.med.inactive")}</Badge>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReportTab({ patientId }: { patientId: string }) {
  const q = useReports(patientId);
  const gen = useGenerateReport(patientId);
  const [openId, setOpenId] = useState<string | null>(null);
  const shown = gen.data ?? q.data?.find((r) => r.id === openId) ?? null;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          disabled={gen.isPending}
          onClick={() => gen.mutate("7d")}
          className="min-h-9 gap-1.5"
        >
          <FileText aria-hidden />
          {gen.isPending ? t("d.report.generating") : t("d.report.generate")}
        </Button>
        <span className="text-muted-foreground text-xs">{t("d.report.hint")}</span>
      </div>
      {gen.isError && <ErrorCard error={gen.error} />}
      {shown && (
        <Card>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              {t("d.report.period")}: {shown.period_start} → {shown.period_end}
              {shown.generated_by && <Badge variant="outline">{shown.generated_by}</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert max-w-none [&_h1]:text-xl [&_h2]:text-lg [&_h2]:font-semibold [&_li]:ml-4 [&_li]:list-disc [&_p]:my-2 [&_table]:my-2 [&_td]:border [&_td]:px-2 [&_th]:border [&_th]:px-2">
            <Markdown>{shown.content_md}</Markdown>
          </CardContent>
        </Card>
      )}
      <h2 className="font-semibold">{t("d.report.previous")}</h2>
      {q.isPending ? (
        <LoadingCard />
      ) : q.isError ? (
        <ErrorCard error={q.error} onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState text={t("d.report.empty")} />
      ) : (
        <ul className="flex flex-col gap-1">
          {q.data.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "justify-start")}
                onClick={() => {
                  gen.reset();
                  setOpenId(r.id);
                }}
              >
                {r.period_start} → {r.period_end} {r.generated_by ? `· ${r.generated_by}` : ""}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
