"use client";

import {
  CalendarCheck,
  CheckSquare,
  ClipboardCheck,
  Dumbbell,
  Pill,
  Smile,
  Square,
} from "lucide-react";
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
      <section className="bg-hero shadow-soft flex flex-col gap-1 rounded-2xl px-5 py-5 text-white">
        <h1 className="text-[1.5em] leading-tight font-bold">
          {t("p.hello", { name: firstName })}
        </h1>
        <p className="text-[0.85em] text-white/85">{t("app.tagline")}</p>
      </section>

      <div className="grid gap-4">
        <BigButton href="/p/talk" emoji="🗣️" label={t("p.talk")} hint={t("p.talk.hint")} />
        <BigButton
          href="/p/exercise"
          emoji="🏋️"
          label={t("p.exercise")}
          hint={t("p.exercise.hint")}
        />
        <BigButton href="/p/say" emoji="🖐️" label={t("p.say")} hint={t("p.say.hint")} />
        <BigButton href="/p/exercise/face" emoji="😊" label={t("p.face")} hint={t("p.face.hint")} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <CalendarCheck aria-hidden className="text-primary size-[1.1em]" />
            {t("p.today")}
          </CardTitle>
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
                      "flex items-center gap-3 rounded-xl border px-3 py-2.5",
                      item.done ? "bg-muted/60" : "bg-card",
                    )}
                  >
                    {item.done ? (
                      <CheckSquare aria-hidden className="text-primary size-[1.4em] shrink-0" />
                    ) : (
                      <Square aria-hidden className="text-muted-foreground size-[1.4em] shrink-0" />
                    )}
                    <span className="bg-accent text-accent-foreground inline-flex size-[1.8em] shrink-0 items-center justify-center rounded-lg">
                      <Icon aria-hidden className="size-[1em]" />
                    </span>
                    <span className="min-w-0 flex-1 leading-snug">
                      {item.title}
                      {item.time ? ` · ${item.time}` : ""}
                    </span>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2.5 py-0.5 text-[0.7em] font-semibold",
                        item.done ? "bg-green-50 text-green-900" : "bg-amber-50 text-amber-900",
                      )}
                    >
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
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <Smile aria-hidden className="text-primary size-[1.1em]" />
            {t("p.mood.title")}
          </CardTitle>
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
                  "bg-card hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-20 flex-col items-center justify-center gap-1 rounded-2xl border-2 px-1 outline-none focus-visible:ring-4 active:translate-y-px disabled:opacity-50",
                  picked === score && "border-primary bg-accent",
                )}
              >
                <span aria-hidden className="text-[1.8em] leading-none">
                  {emoji}
                </span>
                <span className="text-[0.65em] leading-tight">{t(`mood.${score}`)}</span>
              </button>
            ))}
          </div>
          {mood.isSuccess && (
            <p role="status" className="text-primary-deep flex items-center gap-2 font-medium">
              <CheckSquare aria-hidden className="size-[1.2em]" />
              {t("p.mood.thanks")}
            </p>
          )}
          {mood.isError && <ErrorCard error={mood.error} />}
        </CardContent>
      </Card>
    </div>
  );
}
