import type { Metadata } from "next";

import { PatientsTable } from "@/features/clinician/components/PatientsTable";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.clinician") };

export default function ClinicianHomePage() {
  return <PatientsTable />;
}
