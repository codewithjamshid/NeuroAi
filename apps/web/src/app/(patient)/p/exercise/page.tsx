import type { Metadata } from "next";

import { ExerciseScreen } from "@/features/sessions/components/ExerciseScreen";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("p.exercise") };

export default function ExercisePage() {
  return <ExerciseScreen />;
}
