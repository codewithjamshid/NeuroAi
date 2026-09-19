import type { Metadata } from "next";

import { CaregiverSettings } from "@/features/caregiver/components/CaregiverSettings";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("c.settings.title") };

export default function CaregiverSettingsPage() {
  return <CaregiverSettings />;
}
