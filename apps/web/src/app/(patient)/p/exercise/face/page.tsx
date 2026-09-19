import type { Metadata } from "next";
import Link from "next/link";

import { ComingSoon } from "@/components/ComingSoon";
import { buttonVariants } from "@/components/ui/button";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: t("face.title") };

// Placeholder: the stretch agent replaces this with the MediaPipe FaceLandmarker screen (DEMO_SCOPE).
export default function FaceExercisePage() {
  return (
    <div className="flex flex-col gap-4">
      <ComingSoon textKey="soon.face" />
      <Link
        href="/p/exercise"
        className={cn(buttonVariants({ variant: "outline" }), "mx-auto min-h-16 text-[1em]")}
      >
        {t("face.back")}
      </Link>
    </div>
  );
}
