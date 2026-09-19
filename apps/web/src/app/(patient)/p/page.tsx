import type { Metadata } from "next";

import { PatientHome } from "@/features/patients/components/PatientHome";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.patient") };

export default function PatientHomePage() {
  return <PatientHome />;
}
