"use client";

import { HeartHandshake, Stethoscope, TriangleAlert, User } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { errorMessage } from "@/lib/api";
import { type I18nKey, t } from "@/lib/i18n";

import { useLogin } from "../hooks";

const DEMO_PASSWORD = "demo1234";
// DEMO_SCOPE fixed decisions: demo accounts (DEMO_MODE assumed on for the hackathon build).
const demoAccounts: { email: string; label: I18nKey; Icon: typeof User }[] = [
  { email: "bemor@demo.uz", label: "role.patient", Icon: User },
  { email: "qizi@demo.uz", label: "role.caregiver", Icon: HeartHandshake },
  { email: "logoped@demo.uz", label: "role.clinician", Icon: Stethoscope },
];

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const loginM = useLogin();

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">{t("login.demo.title")}</CardTitle>
          <CardDescription>{t("login.demo.text")}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          {demoAccounts.map(({ email: e, label, Icon }) => (
            <Button
              key={e}
              size="lg"
              className="min-h-24 flex-col gap-1 text-lg"
              disabled={loginM.isPending}
              onClick={() => loginM.mutate({ email: e, password: DEMO_PASSWORD })}
            >
              <Icon aria-hidden className="size-8" />
              {t(label)}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">{t("login.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-3"
            onSubmit={(ev) => {
              ev.preventDefault();
              loginM.mutate({ email, password });
            }}
          >
            <label className="flex flex-col gap-1">
              <span className="text-sm font-medium">{t("login.email")}</span>
              <input
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-input bg-background min-h-11 rounded-md border px-3"
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
                className="border-input bg-background min-h-11 rounded-md border px-3"
              />
            </label>
            <Button type="submit" size="lg" className="min-h-11" disabled={loginM.isPending}>
              {loginM.isPending ? t("login.pending") : t("auth.login")}
            </Button>
          </form>
          {loginM.isError && (
            <p role="alert" className="text-destructive mt-3 flex items-center gap-2">
              <TriangleAlert aria-hidden className="size-5 shrink-0" />
              {errorMessage(loginM.error)}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
