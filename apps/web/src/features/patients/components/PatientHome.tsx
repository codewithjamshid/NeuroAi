"use client";

import { CheckSquare, ClipboardCheck, Dumbbell, Pill, Square } from "lucide-react";
import { useState } from "react";

import { BigButton } from "@/components/BigButton";
import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth, useMe } from "@/features/auth/hooks";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useMoodMutation, usePatientId, useToday } from "../hooks";
import type { TodayItem } from "../types";

const MOODS = [
  { score: 1, emoji: "😢" },
  { score: 2, emoji: "😟" },
  { score: 3, emoji: "😐" },
  { score: 4, emoji: "🙂" },
  { score: 5, emoji: "😄" },
] as const;

const kindIcon: Record<TodayItem["kind"], typeof Dumbbell> = {
  exercise: Dumbbell,
  medication: Pill,
  checkin: ClipboardCheck,
};

export function PatientHome() {
  const { user } = useAuth();
  useMe();
  const { patientId, isPending: pidPending, error: pidError } = usePatientId();
  const today = useToday(patientId);
  const mood = useMoodMutation(patientId);
  const [picked, setPicked] = useState<number | null>(null);

  const firstName = user?.full_name?.split(" ")[0] ?? "";

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-[1.5em] font-bold">{t("p.hello", { name: firstName })}</h1>

      <div className="grid gap-4">
        <BigButton href="/p/talk" emoji="🗣️" label={t("p.talk")} hint={t("p.talk.hint")} />
        <BigButton
          href="/p/exercise"
          emoji="🏋️"
          label={t("p.exercise")}
          hint={t("p.exercise.hint")}
        />
        <BigButton href="/p/say" emoji="🖐️" label={t("p.say")} hint={t("p.say.hint")} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-[1.2em]">{t("p.today")}</CardTitle>
        </CardHeader>
        <CardContent>
          {pidError ? (
            <ErrorCard error={pidError} />
          ) : !patientId && !pidPending ? (
            <EmptyState text={t("p.no_patient")} />
          ) : today.isPending ? (
            <LoadingCard />
          ) : today.isError ? (
            <ErrorCard error={today.error} onRetry={() => today.refetch()} />
          ) : today.data.items.length === 0 ? (
            <EmptyState text={t("p.today.empty")} />
          ) : (
            <ul className="flex flex-col gap-2">
              {today.data.items.map((item) => {
                const Icon = kindIcon[item.kind] ?? ClipboardCheck;
                return (
                  <li
                    key={item.id}
                    className={cn(
                      "flex items-center gap-3 rounded-xl border px-3 py-2",
                      item.done && "bg-muted",
                    )}
                  >
                    {item.done ? (
                      <CheckSquare aria-hidden className="size-[1.4em] shrink-0 text-teal-800" />
                    ) : (
                      <Square aria-hidden className="size-[1.4em] shrink-0" />
                    )}
                    <Icon aria-hidden className="size-[1.2em] shrink-0" />
                    <span className="flex-1">
                      {item.title}
                      {item.time ? ` · ${item.time}` : ""}
                    </span>
                    <span className="text-muted-foreground text-[0.85em]">
                      {item.done ? t("p.today.done") : t("p.today.pending")}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-[1.2em]">{t("p.mood.title")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid grid-cols-5 gap-2">
            {MOODS.map(({ score, emoji }) => (
              <button
                key={score}
                type="button"
                aria-label={t(`mood.${score}`)}
                aria-pressed={picked === score}
                disabled={!patientId || mood.isPending}
                onClick={() => {
                  setPicked(score);
                  mood.mutate(score);
                }}
                className={cn(
                  "focus-visible:ring-ring flex min-h-20 flex-col items-center justify-center rounded-xl border-2 outline-none focus-visible:ring-4 disabled:opacity-50",
                  picked === score && "border-teal-700 bg-teal-50 dark:bg-teal-950",
                )}
              >
                <span aria-hidden className="text-[1.8em] leading-none">
                  {emoji}
                </span>
                <span className="text-[0.7em]">{t(`mood.${score}`)}</span>
              </button>
            ))}
          </div>
          {mood.isSuccess && <p role="status">{t("p.mood.thanks")}</p>}
          {mood.isError && <ErrorCard error={mood.error} />}
        </CardContent>
      </Card>
    </div>
  );
}
