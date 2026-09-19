"use client";

import { Activity, Dumbbell, Flag, Pill } from "lucide-react";
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
import { cn } from "@/lib/utils";

// dataviz reference palette: categorical slots in fixed order (blue, orange, aqua, yellow);
// one chart = one measure (no dual axes); 2px lines, ≥ 8px markers, recessive grid, tooltip on hover.
const SERIES = { blue: "#2a78d6", orange: "#eb6834", aqua: "#1baf7a", yellow: "#eda100" } as const;
const GRID = "#e5e1d8";
const AXIS = "#898781";
const TOOLTIP_STYLE = {
  borderRadius: 10,
  border: "1px solid #e5e1d8",
  boxShadow: "0 8px 24px rgba(15,118,110,.08)",
  fontSize: 12,
};

function shortDate(d: string): string {
  return d.length >= 10 ? d.slice(5, 10) : d;
}

function pctTick(v: number): string {
  return `${Math.round(v * 100)}%`;
}

// The API reports adherence as percentages (0–100); charts and tiles work in fractions (0–1).
function asFraction<T extends number | null | undefined>(v: T): T {
  return (typeof v === "number" && v > 1 ? v / 100 : v) as T;
}

type Key = keyof Omit<DashboardDay, "date">;

function ChartTitle({ title, color }: { title: string; color?: string }) {
  return (
    <CardTitle className="flex items-center gap-2">
      {color && (
        <span
          aria-hidden
          className="inline-block size-2.5 rounded-full"
          style={{ background: color }}
        />
      )}
      {title}
    </CardTitle>
  );
}

function StatTile({
  Icon,
  label,
  value,
  unit,
  sub,
  tone,
}: {
  Icon: typeof Activity;
  label: string;
  value: string;
  unit?: string;
  sub?: string;
  tone?: "default" | "alert";
}) {
  return (
    <Card size="sm">
      <CardContent className="flex items-start gap-3">
        <span
          aria-hidden
          className={cn(
            "inline-flex size-9 shrink-0 items-center justify-center rounded-lg",
            tone === "alert" ? "bg-red-50 text-red-800" : "bg-accent text-accent-foreground",
          )}
        >
          <Icon className="size-4" />
        </span>
        <div className="flex min-w-0 flex-col">
          <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
            {label}
          </p>
          <p className="text-2xl leading-tight font-semibold tabular-nums">
            {value}
            {unit && <span className="text-muted-foreground ml-1 text-sm font-normal">{unit}</span>}
          </p>
          {sub && <p className="text-muted-foreground text-xs">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

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
        <ChartTitle title={title} color={color} />
      </CardHeader>
      <CardContent>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={shortDate}
                stroke={AXIS}
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                domain={domain}
                tickFormatter={percent ? pctTick : undefined}
                stroke={AXIS}
                fontSize={11}
                width={48}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
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
  const days = (data.days ?? []).map((d) => ({
    ...d,
    adherence_exercise: asFraction(d.adherence_exercise),
    adherence_medication: asFraction(d.adherence_medication),
  }));
  const flagDates = (data.flags ?? [])
    .map((f) => (f.created_at ?? "").slice(0, 10))
    .filter((d) => days.some((x) => x.date === d));
  const adherence = {
    exercise: asFraction(data.adherence_week?.exercise),
    medication: asFraction(data.adherence_week?.medication),
  };
  const openFlags = (data.flags ?? []).filter((f) => f.status === "open").length;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          Icon={Activity}
          label={t("d.stat.sessions")}
          value={String(data.sessions_count ?? 0)}
          unit={t("d.stat.unit.count")}
          sub={t("d.stat.period")}
        />
        <StatTile
          Icon={Dumbbell}
          label={t("d.stat.adherence_exercise")}
          value={
            adherence.exercise === null || adherence.exercise === undefined
              ? "—"
              : pctTick(adherence.exercise)
          }
          sub={t("d.stat.unit.week")}
        />
        <StatTile
          Icon={Pill}
          label={t("d.stat.adherence_medication")}
          value={
            adherence.medication === null || adherence.medication === undefined
              ? "—"
              : pctTick(adherence.medication)
          }
          sub={t("d.stat.unit.week")}
        />
        <StatTile
          Icon={Flag}
          label={t("d.stat.flags")}
          value={String((data.flags ?? []).length)}
          unit={t("d.stat.unit.count")}
          sub={`${t("flag.status.open")}: ${openFlags}`}
          tone={openFlags > 0 ? "alert" : "default"}
        />
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
          <ChartTitle title={t("d.chart.adherence")} />
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={days} margin={{ top: 8, right: 12, bottom: 0, left: -12 }} barGap={2}>
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={shortDate}
                  stroke={AXIS}
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={pctTick}
                  stroke={AXIS}
                  fontSize={11}
                  width={48}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(v) => (typeof v === "number" ? pctTick(v) : "—")}
                />
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
              <Flag aria-hidden className="size-4 text-red-800" />
              {t("d.tab.flags")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5">
              {data.flags.map((f) => (
                <li key={f.id} className="flex flex-wrap items-center gap-2">
                  <span className="text-muted-foreground font-mono text-xs">
                    {(f.created_at ?? "").slice(0, 10)}
                  </span>
                  <span className="font-medium">{tk(`flag.category.${f.category}`)}</span>
                  <span className="bg-muted rounded-full px-2 py-0.5 text-xs">
                    {tk(`flag.severity.${f.severity}`)}
                  </span>
                  <span className="bg-muted rounded-full px-2 py-0.5 text-xs">
                    {tk(`flag.status.${f.status}`)}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
