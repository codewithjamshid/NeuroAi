"use client";

import dynamic from "next/dynamic";

import { LoadingCard } from "@/components/ErrorCard";
import { t } from "@/lib/i18n";

// MediaPipe touches window/WebGL: load the screen client-side only, and only on this route.
const FaceExerciseScreen = dynamic(
  () => import("./FaceExerciseScreen").then((m) => m.FaceExerciseScreen),
  { ssr: false, loading: () => <LoadingCard text={t("common.loading")} /> },
);

export function FaceExerciseLoader() {
  return <FaceExerciseScreen />;
}
