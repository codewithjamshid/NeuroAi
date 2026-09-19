import type { Metadata } from "next";

import { TalkScreen } from "@/features/sessions/components/TalkScreen";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("p.talk") };

export default function TalkPage() {
  return <TalkScreen />;
}
