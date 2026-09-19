import type { Metadata } from "next";

import { LandingPage } from "@/features/landing/LandingPage";
import { lt } from "@/features/landing/i18n";

export const metadata: Metadata = {
  title: { absolute: lt("meta.title") },
  description: lt("meta.description"),
};

// "/" is the public landing; role screens live under /p, /c, /d behind /login.
export default function HomePage() {
  return <LandingPage />;
}
