import type { Metadata } from "next";

import { SayScreen } from "@/features/interpreter/components/SayScreen";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("c.nav.say") };

// Same interpreter UI as /p/say; mirror mode polls the latest interpretation every 2 s (DEMO_SCOPE).
export default function CaregiverSayPage() {
  return (
    <div className="patient-ui flex flex-1 flex-col">
      <SayScreen mirror boardHref="/p/board" />
    </div>
  );
}
