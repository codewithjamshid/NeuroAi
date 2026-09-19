import type { Metadata } from "next";

import { ComingSoon } from "@/components/ComingSoon";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.patient") };

export default function PatientHomePage() {
  return <ComingSoon textKey="soon.patient" />;
}
