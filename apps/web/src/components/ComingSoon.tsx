import { Construction } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type I18nKey, t } from "@/lib/i18n";

export function ComingSoon({ textKey }: { textKey: I18nKey }) {
  return (
    <Card className="mx-auto w-full max-w-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-[1.2em]">
          <span className="inline-flex size-[2em] shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-800">
            <Construction aria-hidden className="size-[1.1em]" />
          </span>
          {t("soon.title")}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-[1em]">{t(textKey)}</CardContent>
    </Card>
  );
}
