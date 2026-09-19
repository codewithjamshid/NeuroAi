"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import { CircleCheck, CircleDashed, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, apiUrl } from "@/lib/api";
import { t } from "@/lib/i18n";

import { useHealth, useProvidersHealth } from "../hooks";

const REFRESH_MS = 5_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// Rows like {"worker": {"mode": "mock", "status": "ok"}} get a readable summary line.
function SummaryRows({ data }: { data: unknown }) {
  if (!isRecord(data)) return null;
  const rows = Object.entries(data).filter(
    ([, v]) => isRecord(v) && ("status" in v || "mode" in v),
  ) as [string, Record<string, unknown>][];
  if (rows.length === 0) return null;

  return (
    <ul className="mb-3 flex flex-col gap-1.5">
      {rows.map(([name, v]) => (
        <li key={name} className="flex flex-wrap items-center gap-2">
          <span className="font-medium">{name}</span>
          {"mode" in v && (
            <Badge variant="secondary">
              {t("status.mode")}: {String(v.mode)}
            </Badge>
          )}
          {"status" in v && (
            <Badge variant="outline">
              {t("status.status")}: {String(v.status)}
            </Badge>
          )}
        </li>
      ))}
    </ul>
  );
}

function StateBadge({ query }: { query: UseQueryResult<unknown, Error> }) {
  if (query.isPending) {
    return (
      <Badge variant="outline" className="gap-1.5">
        <CircleDashed aria-hidden className="animate-spin" />
        {t("status.loading")}
      </Badge>
    );
  }
  if (query.isError) {
    const code = query.error instanceof ApiError ? query.error.code : "error";
    return (
      <Badge variant="destructive" className="gap-1.5">
        <TriangleAlert aria-hidden />
        {t("status.error")} ({code})
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="gap-1.5 border-teal-700 text-teal-800 dark:text-teal-300">
      <CircleCheck aria-hidden />
      {t("status.ok")}
    </Badge>
  );
}

function EndpointCard({
  title,
  path,
  query,
}: {
  title: string;
  path: string;
  query: UseQueryResult<unknown, Error>;
}) {
  const updated = query.dataUpdatedAt ? new Date(query.dataUpdatedAt).toLocaleTimeString() : null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-mono">{title}</span>
          <StateBadge query={query} />
        </CardTitle>
        <CardDescription className="font-mono text-xs break-all">{apiUrl(path)}</CardDescription>
      </CardHeader>
      <CardContent>
        <SummaryRows data={query.data} />
        <pre className="bg-muted max-h-80 overflow-auto rounded-md p-3 font-mono text-xs">
          {query.data !== undefined ? JSON.stringify(query.data, null, 2) : "—"}
        </pre>
        {updated && (
          <p className="text-muted-foreground mt-2 text-xs">
            {t("status.updated")}: {updated}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function StatusPanel() {
  const health = useHealth(REFRESH_MS);
  const providers = useProvidersHealth(REFRESH_MS);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <EndpointCard title={t("status.health")} path="/health" query={health} />
      <EndpointCard title={t("status.providers")} path="/health/providers" query={providers} />
    </div>
  );
}
