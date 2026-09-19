import { Construction } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type I18nKey, t } from "@/lib/i18n";

export function ComingSoon({ textKey }: { textKey: I18nKey }) {
  return (
    <Card className="mx-auto w-full max-w-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-[1.2em]">
          <Construction aria-hidden className="size-[1.2em]" />
          {t("soon.title")}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-[1em]">{t(textKey)}</CardContent>
    </Card>
  );
}
