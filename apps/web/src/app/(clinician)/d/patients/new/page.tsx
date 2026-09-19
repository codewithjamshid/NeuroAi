import type { Metadata } from "next";

import { NewPatientForm } from "@/features/clinician/components/NewPatientForm";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("d.new.title") };

export default function NewPatientPage() {
  return <NewPatientForm />;
}
