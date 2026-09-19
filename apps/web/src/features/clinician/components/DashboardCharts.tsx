"use client";

import { Flag } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Dashboard, DashboardDay } from "@/features/patients/types";
import { t, tk } from "@/lib/i18n";

// dataviz reference palette: categorical slots in fixed order (blue, orange, aqua, yellow);
// one chart = one measure (no dual axes); 2px lines, ≥ 8px markers, recessive grid, tooltip on hover.
const SERIES = { blue: "#2a78d6", orange: "#eb6834", aqua: "#1baf7a", yellow: "#eda100" } as const;
const GRID = "#e1e0d9";
const AXIS = "#898781";

function shortDate(d: string): string {
  return d.length >= 10 ? d.slice(5, 10) : d;
}

function pctTick(v: number): string {
  return `${Math.round(v * 100)}%`;
}

type Key = keyof Omit<DashboardDay, "date">;

function MetricChart({
  title,
  data,
  dataKey,
  color,
  domain,
  percent,
  flagDates,
  baseline,
  extra,
}: {
  title: string;
  data: DashboardDay[];
  dataKey: Key;
  color: string;
  domain: [number, number];
  percent?: boolean;
  flagDates?: string[];
  baseline?: number | null;
  extra?: { dataKey: Key; color: string; label: string };
}) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="date" tickFormatter={shortDate} stroke={AXIS} fontSize={11} />
              <YAxis
                domain={domain}
                tickFormatter={percent ? pctTick : undefined}
                stroke={AXIS}
                fontSize={11}
                width={48}
              />
              <Tooltip
                labelFormatter={(l) => String(l)}
                formatter={(v) =>
                  percent && typeof v === "number" ? pctTick(v) : String(v ?? "—")
                }
              />
              {extra && <Legend />}
              {flagDates?.map((d) => (
                <ReferenceLine key={d} x={d} stroke="#d03b3b" strokeDasharray="4 4" />
              ))}
              {typeof baseline === "number" && (
                <ReferenceLine
                  y={baseline}
                  stroke={AXIS}
                  strokeDasharray="2 4"
                  label={t("d.chart.baseline")}
                />
              )}
              <Line
                type="monotone"
                dataKey={dataKey}
                name={title}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 4, fill: color, strokeWidth: 0 }}
                connectNulls
                isAnimationActive={false}
              />
              {extra && (
                <Line
                  type="monotone"
                  dataKey={extra.dataKey}
                  name={extra.label}
                  stroke={extra.color}
                  strokeWidth={2}
                  strokeDasharray="6 3"
                  dot={{ r: 4, fill: extra.color, strokeWidth: 0 }}
                  connectNulls
                  isAnimationActive={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardCharts({ data }: { data: Dashboard }) {
  const days = data.days ?? [];
  const flagDates = (data.flags ?? [])
    .map((f) => (f.created_at ?? "").slice(0, 10))
    .filter((d) => days.some((x) => x.date === d));
  const adherence = data.adherence_week ?? {};

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Card size="sm">
          <CardContent>
            <p className="text-muted-foreground">{t("d.stat.sessions")}</p>
            <p className="text-2xl font-semibold">{data.sessions_count ?? 0}</p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent>
            <p className="text-muted-foreground">{t("d.stat.adherence_exercise")}</p>
            <p className="text-2xl font-semibold">
              {adherence.exercise === null || adherence.exercise === undefined
                ? "—"
                : pctTick(adherence.exercise)}
            </p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent>
            <p className="text-muted-foreground">{t("d.stat.adherence_medication")}</p>
            <p className="text-2xl font-semibold">
              {adherence.medication === null || adherence.medication === undefined
                ? "—"
                : pctTick(adherence.medication)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <MetricChart
          title={t("d.chart.speech_accuracy")}
          data={days}
          dataKey="speech_accuracy"
          color={SERIES.blue}
          domain={[0, 1]}
          percent
          flagDates={flagDates}
        />
        <MetricChart
          title={t("d.chart.independence")}
          data={days}
          dataKey="independence"
          color={SERIES.orange}
          domain={[0, 1]}
          percent
        />
        <MetricChart
          title={t("d.chart.fsi")}
          data={days}
          dataKey="fsi"
          color={SERIES.aqua}
          domain={[0, 1]}
          percent
          baseline={data.fsi_base}
        />
        <MetricChart
          title={t("d.chart.mood_self")}
          data={days}
          dataKey="mood_self"
          color={SERIES.yellow}
          domain={[0, 5]}
          extra={{ dataKey: "valence", color: SERIES.blue, label: t("d.chart.valence") }}
        />
      </div>

      <Card size="sm">
        <CardHeader>
          <CardTitle>{t("d.chart.adherence")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={days} margin={{ top: 8, right: 12, bottom: 0, left: -12 }} barGap={2}>
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} stroke={AXIS} fontSize={11} />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={pctTick}
                  stroke={AXIS}
                  fontSize={11}
                  width={48}
                />
                <Tooltip formatter={(v) => (typeof v === "number" ? pctTick(v) : "—")} />
                <Legend />
                <Bar
                  dataKey="adherence_exercise"
                  name={t("d.stat.adherence_exercise")}
                  fill={SERIES.blue}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                />
                <Bar
                  dataKey="adherence_medication"
                  name={t("d.stat.adherence_medication")}
                  fill={SERIES.orange}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {data.flags && data.flags.length > 0 && (
        <Card size="sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flag aria-hidden className="size-4" />
              {t("d.tab.flags")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1">
              {data.flags.map((f) => (
                <li key={f.id} className="flex flex-wrap gap-2">
                  <span className="text-muted-foreground">{(f.created_at ?? "").slice(0, 10)}</span>
                  <span className="font-medium">{tk(`flag.category.${f.category}`)}</span>
                  <span>· {tk(`flag.severity.${f.severity}`)}</span>
                  <span>· {tk(`flag.status.${f.status}`)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
