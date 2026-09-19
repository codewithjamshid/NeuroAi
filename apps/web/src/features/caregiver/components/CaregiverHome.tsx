"use client";

import { Flag, History, Lightbulb, MessageSquareText, Settings } from "lucide-react";
import Link from "next/link";

import { EmptyState, ErrorCard, LoadingCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatient, usePatientId } from "@/features/patients/hooks";
import { StatePanel } from "@/features/sessions/components/StatePanel";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useCaregiverToday, useTips } from "../hooks";

const MOOD_EMOJI = ["", "😢", "😟", "😐", "🙂", "😄"];

export function CaregiverHome() {
  const { patientId, isPending: pidPending, error: pidError } = usePatientId();
  const patient = usePatient(patientId);
  const today = useCaregiverToday(patientId);
  const tips = useTips(patientId);

  const tipList = tips.data?.tips ?? today.data?.tips_cached ?? [];

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">{patient.data?.full_name ?? t("role.caregiver")}</h1>

      {pidError ? (
        <ErrorCard error={pidError} />
      ) : !patientId && !pidPending ? (
        <EmptyState text={t("p.no_patient")} />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("c.today")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {today.isPending && patientId ? (
            <LoadingCard />
          ) : today.isError ? (
            <ErrorCard error={today.error} onRetry={() => today.refetch()} />
          ) : today.data ? (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-3xl" aria-hidden>
                  {today.data.mood_self ? MOOD_EMOJI[today.data.mood_self] : "—"}
                </span>
                <span>
                  {t("c.mood")}:{" "}
                  <strong>
                    {today.data.mood_self ? tk(`mood.${today.data.mood_self}`) : t("c.mood.none")}
                  </strong>
                </span>
              </div>
              <p>
                {t("c.exercises")}:{" "}
                <strong>
                  {today.data.exercises_done}/{today.data.exercises_planned}
                </strong>
              </p>
              <div className="flex items-center gap-2">
                <Flag aria-hidden className="size-4" />
                {t("c.flags_open")}:
                <Badge variant={today.data.flags_open > 0 ? "destructive" : "outline"}>
                  {today.data.flags_open}
                </Badge>
              </div>
              {today.data.state && <StatePanel state={today.data.state} className="text-sm" />}
            </>
          ) : null}
        </CardContent>
      </Card>

      <section className="flex flex-col gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Lightbulb aria-hidden className="size-5" />
          {t("c.tips")}
        </h2>
        {tips.isPending && patientId && tipList.length === 0 ? (
          <LoadingCard />
        ) : tips.isError && tipList.length === 0 ? (
          <ErrorCard error={tips.error} onRetry={() => tips.refetch()} />
        ) : tipList.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid gap-2">
            {tipList.slice(0, 3).map((tip, i) => (
              <Card key={i} size="sm">
                <CardContent>{tip}</CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <MessageSquareText aria-hidden className="size-5" />
          {t("c.last_interpretations")}
        </h2>
        {today.data?.last_interpretations?.length ? (
          <ul className="flex flex-col gap-2">
            {today.data.last_interpretations.map((it) => (
              <li key={it.id} className="rounded-lg border px-3 py-2">
                <p className="font-medium">
                  {it.spoken_text ?? it.chosen ?? it.raw_transcript ?? "—"}
                </p>
                {it.family_note && (
                  <p className="text-muted-foreground text-sm">{it.family_note}</p>
                )}
                <p className="text-muted-foreground text-xs">
                  {new Date(it.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState text={t("c.say.none")} />
        )}
      </section>

      <nav className="grid gap-2">
        <Link
          href="/c/say"
          className={cn(buttonVariants({ size: "lg" }), "min-h-14 gap-2 text-base")}
        >
          <MessageSquareText aria-hidden className="size-5" />
          {t("c.nav.say")}
        </Link>
        <Link
          href="/c/history"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            "min-h-14 gap-2 text-base",
          )}
        >
          <History aria-hidden className="size-5" />
          {t("c.nav.history")}
        </Link>
        <Link
          href="/c/settings"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            "min-h-14 gap-2 text-base",
          )}
        >
          <Settings aria-hidden className="size-5" />
          {t("c.nav.settings")}
        </Link>
      </nav>
    </div>
  );
}
