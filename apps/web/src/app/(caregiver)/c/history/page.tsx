import type { Metadata } from "next";

import { CaregiverHistory } from "@/features/caregiver/components/CaregiverHistory";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("c.history.title") };

export default function CaregiverHistoryPage() {
  return <CaregiverHistory />;
}
