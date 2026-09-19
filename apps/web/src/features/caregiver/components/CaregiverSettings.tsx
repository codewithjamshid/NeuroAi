"use client";

import { CircleCheck, CircleDashed, Send, Settings, User } from "lucide-react";

import { ErrorCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatient, usePatientId } from "@/features/patients/hooks";
import { t, tk } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useTelegramLink, useTelegramStatus } from "../hooks";

// /c/settings — Telegram link code (DEMO_SCOPE: flags only + link code) and patient profile.
export function CaregiverSettings() {
  const link = useTelegramLink();
  const status = useTelegramStatus(link.isSuccess ? 5000 : undefined);
  const { patientId } = usePatientId();
  const patient = usePatient(patientId);
  const linked = status.data?.linked === true;

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-0.5">
        <h1 className="flex items-center gap-2 text-2xl">
          <Settings aria-hidden className="text-primary size-6" />
          {t("c.settings.title")}
        </h1>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2 text-lg">
            <span className="flex items-center gap-2">
              <span
                aria-hidden
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-lg bg-sky-50 text-sky-800"
              >
                <Send className="size-4" />
              </span>
              {t("c.telegram.title")}
            </span>
            {status.isPending ? (
              <Badge variant="outline" className="gap-1">
                <CircleDashed aria-hidden data-motion className="animate-spin" />
                {t("status.loading")}
              </Badge>
            ) : linked ? (
              <Badge variant="outline" className="gap-1 border-teal-300 bg-teal-50 text-teal-900">
                <CircleCheck aria-hidden />
                {t("c.telegram.linked")}
              </Badge>
            ) : (
              <Badge variant="secondary">{t("c.telegram.not_linked")}</Badge>
            )}
          </CardTitle>
          <CardDescription>{t("c.telegram.desc")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {status.isError && <ErrorCard error={status.error} onRetry={() => status.refetch()} />}
          <Button
            onClick={() => link.mutate()}
            disabled={link.isPending}
            className="min-h-11 gap-2"
          >
            <Send aria-hidden />
            {t("c.telegram.get_code")}
          </Button>
          {link.isError && <ErrorCard error={link.error} />}
          {link.data && (
            <div className="bg-muted/70 flex flex-col gap-3 rounded-xl p-4">
              <p className="text-sm">{t("c.telegram.instruction")}</p>
              <div className="flex flex-col gap-1">
                <span className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                  {t("c.telegram.code_label")}
                </span>
                <code className="bg-card block rounded-lg border px-4 py-3 text-center font-mono text-2xl font-semibold tracking-wider select-all">
                  /start {link.data.code}
                </code>
              </div>
              {link.data.bot_username && (
                <a
                  className={cn(buttonVariants({ variant: "outline" }), "min-h-11 gap-2")}
                  href={`https://t.me/${link.data.bot_username}?start=${encodeURIComponent(link.data.code)}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Send aria-hidden />
                  {t("c.telegram.open_bot")} · @{link.data.bot_username}
                </a>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <span
              aria-hidden
              className="bg-accent text-accent-foreground inline-flex size-8 shrink-0 items-center justify-center rounded-lg"
            >
              <User className="size-4" />
            </span>
            {t("c.profile.title")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {patient.isError ? (
            <ErrorCard error={patient.error} />
          ) : patient.data ? (
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted-foreground">{t("patient.full_name")}</dt>
              <dd className="font-medium">{patient.data.full_name}</dd>
              <dt className="text-muted-foreground">{t("patient.birth_year")}</dt>
              <dd className="font-medium">{patient.data.birth_year ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("patient.aphasia_type")}</dt>
              <dd className="font-medium">
                {patient.data.aphasia_type ? tk(`aphasia.${patient.data.aphasia_type}`) : "—"}
              </dd>
              <dt className="text-muted-foreground">{t("patient.dialect")}</dt>
              <dd className="font-medium">
                {patient.data.dialect ? tk(`dialect.${patient.data.dialect}`) : "—"}
              </dd>
            </dl>
          ) : (
            <p className="text-muted-foreground">{t("p.no_patient")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
