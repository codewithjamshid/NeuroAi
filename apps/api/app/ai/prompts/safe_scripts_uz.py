"""Safe reply scripts (TZ §6.3) used INSTEAD of the LLM reply when risk.level == high."""

DEFAULT_CAREGIVER = "parvarishchingiz"


def _who(caregiver: str | None) -> str:
    name = (caregiver or "").strip()
    return name or DEFAULT_CAREGIVER


def self_harm_script(caregiver: str | None = None) -> str:
    """A — o'ziga zarar: short, warm, no methods, no lecture; caregiver is notified."""
    who = _who(caregiver)
    return (
        "Men siz bilanman. Sizni eshityapman. "
        f"Hozir {who}ga xabar beryapman, u yoningizga keladi. "
        "Birga sekin nafas olaylik."
    )


def stroke_signs_script(caregiver: str | None = None, emergency_number: str = "103") -> str:
    """B — yangi insult belgilari (FAST): check, notify family, remind 103. No diagnosis."""
    who = _who(caregiver)
    return (
        "Keling, tekshiramiz: ikkala qo'lingizni ko'taring… tabassum qiling… "
        "'Bugun havo yaxshi' deng. "
        f"Oilangizga ({who}) xabar berdim. "
        f"Bu yangi belgi bo'lsa, tez yordam ({emergency_number}) chaqirish kerak."
    )


def fall_script(caregiver: str | None = None) -> str:
    """C — yiqilish: stay still, name the painful spot, caregiver notified."""
    return f"Qimirlamang, og'riyotgan joyni ayting. {_who(caregiver)}ga xabar berdim."


def medication_reply() -> str:
    """Any medication question → clinician decides (suggested_action=notify_clinician)."""
    return "Bu haqda vrachingiz hal qiladi. Men vrachga xabar qilib qo'yaman."


def safe_script(
    category: str, caregiver: str | None = None, emergency_number: str = "103"
) -> str | None:
    """Dispatch by Risk.category; None when no script applies (abuse → clinician only)."""
    if category == "self_harm":
        return self_harm_script(caregiver)
    if category == "stroke_signs":
        return stroke_signs_script(caregiver, emergency_number)
    if category == "fall":
        return fall_script(caregiver)
    if category == "medication":
        return medication_reply()
    return None
