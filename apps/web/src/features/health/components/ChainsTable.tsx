"use client";

import { ChevronRight, CircleCheck, CircleDashed, CircleOff, CircleX } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

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

// Chip look per circuit state (icon + text, never colour alone).
function chipMeta(circuit: string | null | undefined, configured: boolean | null) {
  if (configured === false) {
    return { Icon: CircleOff, cls: "border-border bg-muted text-muted-foreground" };
  }
  switch (circuit) {
    case "closed":
      return { Icon: CircleCheck, cls: "border-green-200 bg-green-50 text-green-900" };
    case "half_open":
      return { Icon: CircleDashed, cls: "border-amber-200 bg-amber-50 text-amber-900" };
    case "open":
      return { Icon: CircleX, cls: "border-red-200 bg-red-50 text-red-900" };
    default:
      return { Icon: CircleCheck, cls: "border-border bg-card text-foreground" };
  }
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
        <CardDescription>{t("status.chain.order_hint")}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        {chains.map((chain) => {
          const rows = data[chain] as ProviderStatus[];
          return (
            <div key={chain} className="flex flex-col gap-2">
              <h3 className="text-muted-foreground font-mono text-xs font-semibold tracking-wide uppercase">
                {chain}
              </h3>
              <ol className="flex flex-wrap items-center gap-1.5">
                {rows.map((p, i) => {
                  const conf = configuredOf(p);
                  const { Icon, cls } = chipMeta(p.circuit, conf);
                  const stateText = p.circuit
                    ? tk(`status.circuit.${p.circuit}`)
                    : conf === false
                      ? t("common.no")
                      : (p.status ?? "—");
                  return (
                    <li key={`${p.name}-${i}`} className="flex items-center gap-1.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
                          cls,
                        )}
                        title={`${t("status.chain.status")}: ${p.status ?? "—"}`}
                      >
                        <span className="font-mono opacity-70">{i + 1}</span>
                        <span className="font-mono font-semibold">{p.name}</span>
                        <Icon aria-hidden className="size-3.5" />
                        <span>{stateText}</span>
                        {typeof p.latency_ms === "number" && (
                          <span className="tabular-nums opacity-70">· {p.latency_ms} ms</span>
                        )}
                      </span>
                      {i < rows.length - 1 && (
                        <ChevronRight aria-hidden className="text-muted-foreground size-3.5" />
                      )}
                    </li>
                  );
                })}
              </ol>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
