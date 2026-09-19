"use client";

import { CircleCheck, CircleDashed, CircleOff, CircleX } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { t } from "@/lib/i18n";

import type { ChainName, ProviderStatus, ProvidersHealthResponse } from "../api";

const CHAINS: ChainName[] = ["llm", "stt", "tts", "voice_emotion"];

function isRows(v: unknown): v is ProviderStatus[] {
  return Array.isArray(v) && v.every((r) => typeof r === "object" && r !== null && "name" in r);
}

function configuredOf(p: ProviderStatus): boolean | null {
  if (typeof p.configured === "boolean") return p.configured;
  if (typeof p.status === "string") return p.status !== "offline";
  return null;
}

function Circuit({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-muted-foreground">—</span>;
  const Icon = value === "closed" ? CircleCheck : value === "half_open" ? CircleDashed : CircleX;
  return (
    <span className="inline-flex items-center gap-1">
      <Icon aria-hidden className="size-3.5" />
      {value}
    </span>
  );
}

// Fallback chains (TZ §4.4): order = priority. Renders nothing if the payload has no chains yet.
export function ChainsTable({ data }: { data: ProvidersHealthResponse | undefined }) {
  if (!data) return null;
  const chains = CHAINS.filter((c) => isRows(data[c]) && (data[c] as ProviderStatus[]).length > 0);
  if (chains.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("status.chains")}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        {chains.map((chain) => (
          <div key={chain}>
            <h3 className="mb-1 font-mono font-semibold uppercase">{chain}</h3>
            <table className="w-full text-left text-xs">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="py-1 pr-2 font-medium">{t("status.chain.name")}</th>
                  <th className="py-1 pr-2 font-medium">{t("status.chain.configured")}</th>
                  <th className="py-1 pr-2 font-medium">{t("status.chain.status")}</th>
                  <th className="py-1 pr-2 font-medium">{t("status.chain.circuit")}</th>
                  <th className="py-1 font-medium">{t("status.chain.latency")}</th>
                </tr>
              </thead>
              <tbody>
                {(data[chain] as ProviderStatus[]).map((p, i) => {
                  const conf = configuredOf(p);
                  return (
                    <tr key={`${p.name}-${i}`} className="border-t">
                      <td className="py-1 pr-2 font-mono">
                        {i + 1}. {p.name}
                      </td>
                      <td className="py-1 pr-2">
                        {conf === null ? (
                          "—"
                        ) : conf ? (
                          <span className="inline-flex items-center gap-1">
                            <CircleCheck aria-hidden className="size-3.5" />
                            {t("common.yes")}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1">
                            <CircleOff aria-hidden className="size-3.5" />
                            {t("common.no")}
                          </span>
                        )}
                      </td>
                      <td className="py-1 pr-2">{p.status ?? "—"}</td>
                      <td className="py-1 pr-2">
                        <Circuit value={p.circuit} />
                      </td>
                      <td className="py-1">
                        {typeof p.latency_ms === "number" ? `${p.latency_ms} ms` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
