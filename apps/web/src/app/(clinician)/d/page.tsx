import type { Metadata } from "next";

import { ComingSoon } from "@/components/ComingSoon";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.clinician") };

export default function ClinicianHomePage() {
  return <ComingSoon textKey="soon.clinician" />;
}
