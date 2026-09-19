"use client";

import { CircleCheck, CircleDashed, Send } from "lucide-react";

import { ErrorCard } from "@/components/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatient, usePatientId } from "@/features/patients/hooks";
import { t } from "@/lib/i18n";

import { useTelegramLink, useTelegramStatus } from "../hooks";

// /c/settings — Telegram link code (DEMO_SCOPE: flags only + link code) and patient profile.
export function CaregiverSettings() {
  const link = useTelegramLink();
  const status = useTelegramStatus(link.isSuccess ? 5000 : undefined);
  const { patientId } = usePatientId();
  const patient = usePatient(patientId);
  const linked = status.data?.linked === true;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">{t("c.settings.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2 text-lg">
            {t("c.telegram.title")}
            {status.isPending ? (
              <Badge variant="outline" className="gap-1">
                <CircleDashed aria-hidden className="animate-spin" />
                {t("status.loading")}
              </Badge>
            ) : linked ? (
              <Badge variant="outline" className="gap-1 border-teal-700 text-teal-800">
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
            <div className="bg-muted flex flex-col gap-2 rounded-lg p-3">
              <p className="text-sm">{t("c.telegram.instruction")}</p>
              <code className="bg-background rounded border px-3 py-2 text-lg font-semibold select-all">
                /start {link.data.code}
              </code>
              {link.data.bot_username && (
                <a
                  className="text-primary underline"
                  href={`https://t.me/${link.data.bot_username}?start=${encodeURIComponent(link.data.code)}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  @{link.data.bot_username}
                </a>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("c.profile.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {patient.isError ? (
            <ErrorCard error={patient.error} />
          ) : patient.data ? (
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted-foreground">{t("patient.full_name")}</dt>
              <dd>{patient.data.full_name}</dd>
              <dt className="text-muted-foreground">{t("patient.birth_year")}</dt>
              <dd>{patient.data.birth_year ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("patient.aphasia_type")}</dt>
              <dd>{patient.data.aphasia_type ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("patient.dialect")}</dt>
              <dd>{patient.data.dialect ?? "—"}</dd>
            </dl>
          ) : (
            <p className="text-muted-foreground">{t("p.no_patient")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
