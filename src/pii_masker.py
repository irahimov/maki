"""Rule-based PII detection and masking.

Detects: e-mail, Azerbaijani IBAN (mod-97 checked), payment card (Luhn checked),
Azerbaijani phone numbers, and FIN codes only when preceded by the word FIN.
Masking keeps the last 4 non-space characters and replaces the rest with '*'.

Limits: precision and recall are measured on synthetic data only. The FIN format
is an assumption and has not been checked against an official specification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

KEEP = 4

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
IBAN = re.compile(r"\bAZ\d{2}(?: ?[A-Z0-9]{4}){6}\b")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
# +994 prefix: detected without context. 0-prefix: only with a phone word or an operator code.
# Operator codes are NOT verified against an official list; see README.
OPERATOR_CODES = ("50", "51", "55", "70", "77", "99")
SEP = r"[ -]?"
PHONE_INTL = re.compile(r"(?<!\d)\+994" + SEP + r"\d{2}" + SEP + r"\d{3}" + SEP + r"\d{2}" + SEP + r"\d{2}(?!\d)")
PHONE_LOCAL = re.compile(
    r"(?:(?i:telefon|tel|mobil)[:\s-]*)?(?<!\d)0(?:" + "|".join(OPERATOR_CODES) + r")"
    + SEP + r"\d{3}" + SEP + r"\d{2}" + SEP + r"\d{2}(?!\d)"
)
FIN = re.compile(r"\b(?:FIN|FİN)\b[:\s-]*([A-Z0-9]{7})\b")


@dataclass(frozen=True)
class Hit:
    kind: str
    start: int
    end: int


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def luhn_check_digit(payload: str) -> str:
    """Digit that makes payload + digit pass Luhn."""
    for d in "0123456789":
        if luhn_ok(payload + d):
            return d
    raise AssertionError("unreachable")


def iban_ok(value: str) -> bool:
    raw = value.replace(" ", "")
    if len(raw) != 28 or not raw.startswith("AZ"):
        return False
    rearranged = raw[4:] + raw[:4]
    number = "".join(str(int(c, 36)) for c in rearranged)
    return int(number) % 97 == 1


def build_iban(bank: str, account: str) -> str:
    """Valid AZ IBAN from a 4-char bank code and a 20-char account (digits or capitals)."""
    body = bank + account
    number = "".join(str(int(c, 36)) for c in body + "AZ00")
    check = 98 - (int(number) % 97)
    return f"AZ{check:02d}{body}"


def _mask(value: str) -> str:
    positions = [i for i, ch in enumerate(value) if not ch.isspace()]
    keep = set(positions[-KEEP:])
    return "".join(ch if (i in keep or ch.isspace()) else "*" for i, ch in enumerate(value))


def find(text: str) -> list[Hit]:
    hits: list[Hit] = []

    def add(kind: str, start: int, end: int) -> None:
        if not any(start < h.end and h.start < end for h in hits):
            hits.append(Hit(kind, start, end))

    for m in IBAN.finditer(text):
        if iban_ok(m.group()):
            add("iban", *m.span())
    for m in EMAIL.finditer(text):
        add("email", *m.span())
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            add("card", *m.span())
    for rx in (PHONE_INTL, PHONE_LOCAL):
        for m in rx.finditer(text):
            add("phone", *m.span())
    for m in FIN.finditer(text):
        add("fin", *m.span(1))
    return sorted(hits, key=lambda h: h.start)


def mask(text: str) -> tuple[str, list[Hit]]:
    hits = find(text)
    out: list[str] = []
    prev = 0
    for h in hits:
        out.append(text[prev:h.start])
        out.append(_mask(text[h.start:h.end]))
        prev = h.end
    out.append(text[prev:])
    return "".join(out), hits
