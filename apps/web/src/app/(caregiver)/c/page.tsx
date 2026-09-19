import type { Metadata } from "next";

import { ComingSoon } from "@/components/ComingSoon";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.caregiver") };

export default function CaregiverHomePage() {
  return <ComingSoon textKey="soon.caregiver" />;
}
