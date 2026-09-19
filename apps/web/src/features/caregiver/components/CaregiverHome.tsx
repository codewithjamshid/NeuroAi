"use client";

import {
  CalendarCheck,
  Dumbbell,
  Flag,
  History,
  Lightbulb,
  MessageSquareText,
  Settings,
  Smile,
} from "lucide-react";
import Link from "next/link";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatient, usePatientId } from "@/features/patients/hooks";
import { StatePanel } from "@/features/sessions/components/StatePanel";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useCaregiverToday, useTips } from "../hooks";

const MOOD_EMOJI = ["", "😢", "😟", "😐", "🙂", "😄"];

function IconBadge({ Icon, className }: { Icon: typeof Flag; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "bg-accent text-accent-foreground inline-flex size-8 shrink-0 items-center justify-center rounded-lg",
        className,
      )}
    >
      <Icon className="size-4" />
    </span>
  );
}

export function CaregiverHome() {
  const { patientId, isPending: pidPending, error: pidError } = usePatientId();
  const patient = usePatient(patientId);
  const today = useCaregiverToday(patientId);
  const tips = useTips(patientId);

  const tipList = tips.data?.tips ?? today.data?.tips_cached ?? [];

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-0.5">
        <p className="text-muted-foreground text-sm">{t("role.caregiver")}</p>
        <h1 className="text-2xl">{patient.data?.full_name ?? t("role.caregiver")}</h1>
      </header>

      {pidError ? (
        <ErrorCard error={pidError} />
      ) : !patientId && !pidPending ? (
        <EmptyState text={t("p.no_patient")} />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <IconBadge Icon={CalendarCheck} />
            {t("c.today")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {today.isPending && patientId ? (
            <LoadingCard />
          ) : today.isError ? (
            <ErrorCard error={today.error} onRetry={() => today.refetch()} />
          ) : today.data ? (
            <>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-muted/60 flex flex-col items-center gap-1 rounded-xl px-2 py-3 text-center">
                  <span className="text-3xl leading-none" aria-hidden>
                    {today.data.mood_self ? MOOD_EMOJI[today.data.mood_self] : "—"}
                  </span>
                  <span className="text-muted-foreground flex items-center gap-1 text-xs">
                    <Smile aria-hidden className="size-3.5" />
                    {t("c.mood")}
                  </span>
                  <span className="text-sm font-semibold">
                    {today.data.mood_self ? tk(`mood.${today.data.mood_self}`) : t("c.mood.none")}
                  </span>
                </div>
                <div className="bg-muted/60 flex flex-col items-center gap-1 rounded-xl px-2 py-3 text-center">
                  <span className="text-3xl leading-none font-semibold">
                    {today.data.exercises_done}
                    <span className="text-muted-foreground text-base font-normal">
                      /{today.data.exercises_planned}
                    </span>
                  </span>
                  <span className="text-muted-foreground flex items-center gap-1 text-xs">
                    <Dumbbell aria-hidden className="size-3.5" />
                    {t("c.exercises")}
                  </span>
                </div>
                <div
                  className={cn(
                    "flex flex-col items-center gap-1 rounded-xl px-2 py-3 text-center",
                    today.data.flags_open > 0 ? "bg-red-50 text-red-950" : "bg-muted/60",
                  )}
                >
                  <span className="text-3xl leading-none font-semibold">
                    {today.data.flags_open}
                  </span>
                  <span
                    className={cn(
                      "flex items-center gap-1 text-xs",
                      today.data.flags_open > 0 ? "text-red-800" : "text-muted-foreground",
                    )}
                  >
                    <Flag aria-hidden className="size-3.5" />
                    {t("c.flags_open")}
                  </span>
                </div>
              </div>
              {today.data.state && <StatePanel state={today.data.state} className="text-sm" />}
            </>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <IconBadge Icon={Lightbulb} className="bg-amber-50 text-amber-800" />
            {t("c.tips")}
          </CardTitle>
          <CardDescription>{t("c.tips.hint")}</CardDescription>
        </CardHeader>
        <CardContent>
          {tips.isPending && patientId && tipList.length === 0 ? (
            <LoadingCard />
          ) : tips.isError && tipList.length === 0 ? (
            <ErrorCard error={tips.error} onRetry={() => tips.refetch()} />
          ) : tipList.length === 0 ? (
            <EmptyState />
          ) : (
            <ol className="flex flex-col gap-2">
              {tipList.slice(0, 3).map((tip, i) => (
                <li key={i} className="bg-muted/60 flex items-start gap-3 rounded-xl px-3 py-3">
                  <span className="bg-primary text-primary-foreground inline-flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
                    {i + 1}
                  </span>
                  <span className="leading-snug">{tip}</span>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <IconBadge Icon={MessageSquareText} />
            {t("c.last_interpretations")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {today.data?.last_interpretations?.length ? (
            <ol className="border-border ml-2 flex flex-col gap-4 border-l-2 pl-5">
              {today.data.last_interpretations.map((it) => (
                <li key={it.id} className="relative">
                  <span
                    aria-hidden
                    className="bg-primary ring-card absolute top-1.5 -left-[27px] size-3 rounded-full ring-4"
                  />
                  <p className="leading-snug font-medium">
                    {it.spoken_text ?? it.chosen ?? it.raw_transcript ?? "—"}
                  </p>
                  {it.family_note && (
                    <p className="text-muted-foreground mt-0.5 text-sm">{it.family_note}</p>
                  )}
                  <p className="text-muted-foreground mt-1 text-xs">
                    {new Date(it.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState text={t("c.say.none")} />
          )}
        </CardContent>
      </Card>

      <nav aria-label={t("c.nav.title")} className="grid grid-cols-3 gap-2">
        <Link
          href="/c/say"
          className="bg-primary text-primary-foreground shadow-soft hover:bg-primary-hover focus-visible:ring-ring flex min-h-20 flex-col items-center justify-center gap-1.5 rounded-xl px-2 py-3 text-center text-sm font-semibold outline-none focus-visible:ring-3 active:translate-y-px"
        >
          <MessageSquareText aria-hidden className="size-6" />
          {t("c.nav.say")}
        </Link>
        <Link
          href="/c/history"
          className="bg-card hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-20 flex-col items-center justify-center gap-1.5 rounded-xl border px-2 py-3 text-center text-sm font-semibold outline-none focus-visible:ring-3 active:translate-y-px"
        >
          <History aria-hidden className="text-primary size-6" />
          {t("c.nav.history")}
        </Link>
        <Link
          href="/c/settings"
          className="bg-card hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-20 flex-col items-center justify-center gap-1.5 rounded-xl border px-2 py-3 text-center text-sm font-semibold outline-none focus-visible:ring-3 active:translate-y-px"
        >
          <Settings aria-hidden className="text-primary size-6" />
          {t("c.nav.settings")}
        </Link>
      </nav>
    </div>
  );
}
