"use client";

import { UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ErrorCard } from "@/components/ErrorCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreatePatient } from "@/features/patients/hooks";
import { t } from "@/lib/i18n";

const inputCls = "field";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

// /d/patients/new — patient card + consent (TZ §8.2). Enum values match apps/api patients/models.py.
export function NewPatientForm() {
  const router = useRouter();
  const create = useCreatePatient();
  const [f, setF] = useState({
    full_name: "",
    birth_year: "",
    sex: "male",
    stroke_date: "",
    affected_side: "unknown",
    aphasia_type: "unknown",
    dialect: "standard",
    interests: "",
    family_members: "",
    consent: false,
  });
  const set =
    (k: keyof typeof f) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setF((s) => ({
        ...s,
        [k]: e.target.type === "checkbox" ? (e.target as HTMLInputElement).checked : e.target.value,
      }));

  return (
    <Card className="mx-auto w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <span
            aria-hidden
            className="bg-accent text-accent-foreground inline-flex size-8 shrink-0 items-center justify-center rounded-lg"
          >
            <UserPlus className="size-4" />
          </span>
          {t("d.new.title")}
        </CardTitle>
        <CardDescription>{t("app.disclaimer")}</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={(ev) => {
            ev.preventDefault();
            if (!f.consent) return;
            create.mutate(
              {
                full_name: f.full_name.trim(),
                birth_year: f.birth_year ? Number(f.birth_year) : null,
                sex: f.sex,
                stroke_date: f.stroke_date || null,
                affected_side: f.affected_side,
                aphasia_type: f.aphasia_type,
                dialect: f.dialect,
                interests: f.interests
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean),
                family_members: f.family_members
                  .split("\n")
                  .map((line) => line.trim())
                  .filter(Boolean)
                  .map((line) => {
                    const [name, relation = ""] = line.split(":").map((s) => s.trim());
                    return { name, relation };
                  }),
                consent: { scopes: { audio_retention: true, data_for_research: false } },
              },
              { onSuccess: (p) => router.replace(`/d/patients/${p.id}`) },
            );
          }}
        >
          <Field label={t("patient.full_name")}>
            <input required className={inputCls} value={f.full_name} onChange={set("full_name")} />
          </Field>
          <Field label={t("patient.birth_year")}>
            <input
              type="number"
              min={1900}
              max={2026}
              className={inputCls}
              value={f.birth_year}
              onChange={set("birth_year")}
            />
          </Field>
          <Field label={t("patient.sex")}>
            <select className={inputCls} value={f.sex} onChange={set("sex")}>
              <option value="male">{t("patient.sex.male")}</option>
              <option value="female">{t("patient.sex.female")}</option>
            </select>
          </Field>
          <Field label={t("patient.stroke_date")}>
            <input
              type="date"
              className={inputCls}
              value={f.stroke_date}
              onChange={set("stroke_date")}
            />
          </Field>
          <Field label={t("patient.affected_side")}>
            <select className={inputCls} value={f.affected_side} onChange={set("affected_side")}>
              <option value="left">{t("side.left")}</option>
              <option value="right">{t("side.right")}</option>
              <option value="both">{t("side.both")}</option>
              <option value="unknown">{t("side.unknown")}</option>
            </select>
          </Field>
          <Field label={t("patient.aphasia_type")}>
            <select className={inputCls} value={f.aphasia_type} onChange={set("aphasia_type")}>
              <option value="motor">{t("aphasia.motor")}</option>
              <option value="sensory">{t("aphasia.sensory")}</option>
              <option value="global">{t("aphasia.global")}</option>
              <option value="amnestic">{t("aphasia.amnestic")}</option>
              <option value="unknown">{t("aphasia.unknown")}</option>
            </select>
          </Field>
          <Field label={t("patient.dialect")}>
            <select className={inputCls} value={f.dialect} onChange={set("dialect")}>
              <option value="standard">{t("dialect.standard")}</option>
              <option value="khorezm">{t("dialect.khorezm")}</option>
              <option value="other">{t("dialect.other")}</option>
            </select>
          </Field>
          <Field label={t("patient.interests")}>
            <input
              className={inputCls}
              placeholder={t("patient.interests.hint")}
              value={f.interests}
              onChange={set("interests")}
            />
          </Field>
          <div className="sm:col-span-2">
            <Field label={t("patient.family_members")}>
              <textarea
                rows={3}
                className={`${inputCls} py-2`}
                placeholder={t("patient.family_members.hint")}
                value={f.family_members}
                onChange={set("family_members")}
              />
            </Field>
          </div>
          <label className="bg-muted/60 flex items-start gap-3 rounded-xl px-3 py-3 sm:col-span-2">
            <input
              type="checkbox"
              required
              className="accent-primary mt-1 size-4"
              checked={f.consent}
              onChange={set("consent")}
            />
            <span>{t("patient.consent")}</span>
          </label>
          {create.isError && (
            <div className="sm:col-span-2">
              <ErrorCard error={create.error} />
            </div>
          )}
          <div className="flex gap-2 sm:col-span-2">
            <Button type="submit" disabled={create.isPending || !f.consent} className="min-h-10">
              {create.isPending ? t("common.saving") : t("common.save")}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="min-h-10"
              onClick={() => router.back()}
            >
              {t("common.cancel")}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
