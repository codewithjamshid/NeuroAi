import type { Metadata } from "next";
import { Suspense } from "react";

import { LoadingCard } from "@/components/ErrorCard";
import { BoardScreen } from "@/features/interpreter/components/BoardScreen";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("board.title") };

// useSearchParams (?iid=) needs a Suspense boundary for static prerender.
export default function BoardPage() {
  return (
    <Suspense fallback={<LoadingCard />}>
      <BoardScreen />
    </Suspense>
  );
}
