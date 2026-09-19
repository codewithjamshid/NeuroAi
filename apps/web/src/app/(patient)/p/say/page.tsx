import type { Metadata } from "next";

import { SayScreen } from "@/features/interpreter/components/SayScreen";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("p.say") };

export default function SayPage() {
  return <SayScreen />;
}
