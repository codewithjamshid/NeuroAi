"use client";

import { ArrowRight, HeartHandshake, LogIn, Stethoscope, TriangleAlert, User } from "lucide-react";
import { useState } from "react";

import { LoadingCard } from "@/components/ErrorCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { errorMessage } from "@/lib/api";
import { type I18nKey, t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useLogin } from "../hooks";

const DEMO_PASSWORD = "demo1234";
// DEMO_SCOPE fixed decisions: demo accounts (DEMO_MODE assumed on for the hackathon build).
const demoAccounts: {
  email: string;
  label: I18nKey;
  desc: I18nKey;
  Icon: typeof User;
  tint: string;
}[] = [
  {
    email: "bemor@demo.uz",
    label: "role.patient",
    desc: "role.patient.desc",
    Icon: User,
    tint: "bg-teal-50 text-teal-800",
  },
  {
    email: "qizi@demo.uz",
    label: "role.caregiver",
    desc: "role.caregiver.desc",
    Icon: HeartHandshake,
    tint: "bg-amber-50 text-amber-800",
  },
  {
    email: "logoped@demo.uz",
    label: "role.clinician",
    desc: "role.clinician.desc",
    Icon: Stethoscope,
    tint: "bg-indigo-50 text-indigo-800",
  },
];

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const loginM = useLogin();

  return (
    <div className="flex flex-col gap-5">
      <Card className="shadow-soft">
        <CardHeader>
          <CardTitle className="text-xl">{t("login.demo.title")}</CardTitle>
          <CardDescription>{t("login.demo.text")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid gap-3 sm:grid-cols-3">
            {demoAccounts.map(({ email: e, label, desc, Icon, tint }) => (
              <button
                key={e}
                type="button"
                disabled={loginM.isPending}
                onClick={() => loginM.mutate({ email: e, password: DEMO_PASSWORD })}
                className="group bg-card hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-32 flex-col items-start gap-2 rounded-xl border p-4 text-left outline-none focus-visible:ring-3 active:translate-y-px disabled:opacity-50"
              >
                <span
                  aria-hidden
                  className={cn("inline-flex size-10 items-center justify-center rounded-lg", tint)}
                >
                  <Icon className="size-5" />
                </span>
                <span className="text-base leading-tight font-semibold">{t(label)}</span>
                <span className="text-muted-foreground text-sm leading-snug">{t(desc)}</span>
                <span className="text-primary mt-auto inline-flex items-center gap-1 text-sm font-medium">
                  {t("login.demo.enter")}
                  <ArrowRight
                    aria-hidden
                    className="size-4 transition-transform group-hover:translate-x-0.5"
                  />
                </span>
              </button>
            ))}
          </div>
          {loginM.isPending && <LoadingCard text={t("login.pending")} />}
        </CardContent>
      </Card>

      <Card className="shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <LogIn aria-hidden className="text-primary size-5" />
            {t("login.title")}
          </CardTitle>
          <CardDescription>{t("login.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-3"
            onSubmit={(ev) => {
              ev.preventDefault();
              loginM.mutate({ email, password });
            }}
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1">
                <span className="text-sm font-medium">{t("login.email")}</span>
                <input
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="field min-h-11"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm font-medium">{t("login.password")}</span>
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="field min-h-11"
                />
              </label>
            </div>
            <Button
              type="submit"
              size="lg"
              className="hover:bg-primary-hover min-h-11 gap-2"
              disabled={loginM.isPending}
            >
              <LogIn aria-hidden />
              {loginM.isPending ? t("login.pending") : t("auth.login")}
            </Button>
          </form>
          {loginM.isError && (
            <p
              role="alert"
              className="text-destructive mt-3 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2"
            >
              <TriangleAlert aria-hidden className="size-5 shrink-0" />
              {errorMessage(loginM.error)}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
