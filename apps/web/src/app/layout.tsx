import type { Metadata, Viewport } from "next";

import { t } from "@/lib/i18n";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: { default: t("app.name"), template: `%s · ${t("app.name")}` },
  description: t("app.tagline"),
  applicationName: t("app.name"),
  appleWebApp: { capable: true, statusBarStyle: "default", title: t("app.name") },
};

export const viewport: Viewport = {
  themeColor: "#0f766e",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="uz">
      <body className="min-h-dvh antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
