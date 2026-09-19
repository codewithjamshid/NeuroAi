import { RoleHeader } from "@/components/RoleHeader";
import { t } from "@/lib/i18n";

// TZ §8.1: phone-first, card based.
export default function CaregiverLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <RoleHeader role={t("role.caregiver")} />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col px-4 py-6">{children}</main>
    </div>
  );
}
