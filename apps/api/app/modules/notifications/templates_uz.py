"""Telegram / in-app message templates (TZ §6.2)."""

CATEGORY_UZ = {
    "self_harm": "o'ziga zarar haqida gap",
    "stroke_signs": "insultning yangi belgilari",
    "fall": "yiqilish / jarohat",
    "medication": "dori bilan bog'liq muammo",
    "abuse": "zo'ravonlik yoki qarovsizlik belgisi",
    "adherence": "kayfiyat / mashqqa rioya pasayishi",
    "other": "e'tibor talab qiladigan holat",
}


def red_flag_message(
    category: str, severity: str, patient: str, evidence: str | None, time: str
) -> str:
    quote = (evidence or "").strip()
    if category == "self_harm":
        return (
            f"🔴 NeuroAI — {patient}: suhbatda o'ziga zarar haqida gap aniqlandi ({time}). "
            "Iltimos, hozir yoniga boring, xotirjam gaplashing, yolg'iz qoldirmang. "
            "Vrachga xabar berildi."
        )
    if category == "stroke_signs":
        return (
            f"🔴 NeuroAI — {patient}: insultning yangi belgilari bo'lishi mumkin: "
            f"{quote or 'nutqda shikoyat'}. Zudlik bilan tekshiring (yuz, qo'l, nutq) va kerak "
            "bo'lsa 103 ga qo'ng'iroq qiling."
        )
    if category == "fall":
        return (
            f"🔴 NeuroAI — {patient}: yiqilish yoki jarohat haqida aytdi ({time})"
            + (f': "{quote}"' if quote else "")
            + ". Iltimos, darhol yoniga boring va holatini tekshiring."
        )
    icon = "🔴" if severity == "high" else "🟠" if severity == "medium" else "🟡"
    what = CATEGORY_UZ.get(category, CATEGORY_UZ["other"])
    tail = f' — "{quote}"' if quote else ""
    return f"{icon} NeuroAI — {patient}: {what} aniqlandi ({time}){tail}. Iltimos, e'tibor bering."


def link_ok(full_name: str) -> str:
    return f"NeuroAI ulandi ✅ ({full_name})"


def link_bad() -> str:
    return "Kod noto'g'ri yoki muddati o'tgan. Ilovada yangi kod oling va /start <kod> yuboring."
