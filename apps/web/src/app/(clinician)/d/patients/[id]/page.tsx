import type { Metadata } from "next";

import { PatientDetail } from "@/features/clinician/components/PatientDetail";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("d.patient.title") };

// Next 15: params is a Promise in server components.
export default async function PatientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PatientDetail patientId={id} />;
}
