import type { Metadata } from "next";

import { CaregiverHome } from "@/features/caregiver/components/CaregiverHome";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("role.caregiver") };

export default function CaregiverHomePage() {
  return <CaregiverHome />;
}
