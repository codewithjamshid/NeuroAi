import { RoleHeader } from "@/components/RoleHeader";
import { t } from "@/lib/i18n";

// TZ §8.1: dense desktop layout (tables + charts).
export default function ClinicianLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <RoleHeader role={t("role.clinician")} />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 text-sm">
        {children}
      </main>
    </div>
  );
}
