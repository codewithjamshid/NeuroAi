import type { Metadata } from "next";

import { FaceExerciseLoader } from "@/features/face/components/FaceExerciseLoader";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("face.title") };

// TZ §8.2 /p/exercise/face — camera, live FSI, rep counter (DEMO_SCOPE stretch).
export default function FaceExercisePage() {
  return <FaceExerciseLoader />;
}
