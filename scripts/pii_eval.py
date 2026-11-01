#!/usr/bin/env python3
"""Synthetic evaluation of src/pii_masker.py: precision and recall per PII kind.

SYNTHETIC DATA ONLY. This generator uses the same formats, check digits and
prefixes that pii_masker looks for, so the numbers measure consistency between
generator and detector, not accuracy on real text. Hard negatives are included
in the score on purpose.
"""
from __future__ import annotations

import json
import random
import string
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import pii_masker as pm  # noqa: E402

SEED = 20261018
N = 1000
OUT = ROOT / "results"
KINDS = ["iban", "card", "phone", "email", "fin"]
BANKS = ["TEST", "DEMO", "SAMP"]  # synthetic 4-letter codes, not real bank codes
PHONE_PREFIX = ["50", "51", "55", "70", "77", "99"]
NEUTRAL = [
    "Müştəri sorğusu qəbul olundu.",
    "Məbləğ 1500.00 AZN təşkil edir.",
    "Tarix 2026-10-18 olaraq qeyd edildi.",
    "Əməliyyat uğurla tamamlandı.",
    "Zəhmət olmasa sənədləri yoxlayın.",
    "Sorğu 3 gün ərzində cavablandırılacaq.",
]
LABEL = {"iban": "IBAN: ", "card": "Kart: ", "phone": "Telefon: ", "email": "E-poçt: ", "fin": "FIN: "}
NEG = {
    "order": "Sifariş nömrəsi: {}.",
    "badcard": "Kart nömrəsi: {}.",
    "badiban": "IBAN: {}.",
    "refcode": "İstinad kodu AB12345 göndərildi.",
}


def digits(r: random.Random, n: int) -> str:
    return "".join(r.choice(string.digits) for _ in range(n))


def value(r: random.Random, kind: str) -> str:
    if kind == "iban":
        acc = "".join(r.choice(string.digits + string.ascii_uppercase) for _ in range(20))
        raw = pm.build_iban(r.choice(BANKS), acc)
        return raw if r.random() < 0.5 else " ".join(raw[i:i + 4] for i in range(0, 28, 4))
    if kind == "card":
        payload = "4" + digits(r, 14)
        raw = payload + pm.luhn_check_digit(payload)
        return r.choice(["", " ", "-"]).join(raw[i:i + 4] for i in range(0, 16, 4))
    if kind == "phone":
        p, body = r.choice(PHONE_PREFIX), digits(r, 7)
        return r.choice([
            f"+994 {p} {body[:3]} {body[3:5]} {body[5:]}",
            f"0{p}-{body[:3]}-{body[3:5]}-{body[5:]}",
            f"0{p}{body}",
        ])
    if kind == "email":
        name = "".join(r.choice(string.ascii_lowercase) for _ in range(r.randint(4, 9)))
        return f"{name}@{r.choice(['example.com', 'example.org', 'test.net'])}"
    return "".join(r.choice(string.ascii_uppercase + string.digits) for _ in range(7))  # fin


def negative(r: random.Random) -> str:
    k = r.choice(list(NEG))
    if k == "order":
        return NEG[k].format("0" + digits(r, 9))
    if k == "badcard":
        payload = "4" + digits(r, 14)
        raw = payload + pm.luhn_check_digit(payload)
        return NEG[k].format(raw[:-1] + str((int(raw[-1]) + 1) % 10))
    if k == "badiban":
        good = pm.build_iban(r.choice(BANKS), digits(r, 20))
        bad = good[:4] + ("0" if good[4] != "0" else "1") + good[5:]
        return NEG[k].format(bad)
    return NEG[k]


def sample(r: random.Random) -> tuple[str, list]:
    pieces: list[tuple[str, str | None]] = []
    for _ in range(r.randint(1, 3)):
        roll = r.random()
        if roll < 0.35:
            pieces.append((r.choice(NEUTRAL) + " ", None))
        elif roll < 0.80:
            kind = r.choice(KINDS)
            pieces.append((LABEL[kind], None))
            pieces.append((value(r, kind), kind))
            pieces.append((". ", None))
        else:
            pieces.append((negative(r) + " ", None))
    text, gold = "", []
    for piece, kind in pieces:
        if kind:
            gold.append((kind, len(text), len(text) + len(piece)))
        text += piece
    return text, gold


def overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def evaluate(samples: list) -> tuple[Counter, Counter, Counter]:
    tp, fp, fn = Counter(), Counter(), Counter()
    for text, gold in samples:
        used: set[int] = set()
        for p in pm.find(text):
            for gi, (k, s, e) in enumerate(gold):
                if gi not in used and k == p.kind and overlap((p.start, p.end), (s, e)):
                    used.add(gi)
                    tp[k] += 1
                    break
            else:
                fp[p.kind] += 1
        for gi, (k, _, _) in enumerate(gold):
            if gi not in used:
                fn[k] += 1
    return tp, fp, fn


def ratio(a: int, b: int) -> str:
    return f"{a / b:.3f}" if b else "n/a"


def report(tp: Counter, fp: Counter, fn: Counter, n_samples: int) -> str:
    total_gold = sum(tp.values()) + sum(fn.values())
    lines = [
        "PII masker: synthetic evaluation",
        "SYNTHETIC DATA ONLY. Generator and detector share formats, check digits and prefixes.",
        "The numbers measure consistency, not accuracy on real text. Hard negatives are included.",
        f"seed={SEED} samples={n_samples} gold_items={total_gold}",
        "",
        f"{'tür':<8}{'TP':>5}{'FP':>5}{'FN':>5}{'precision':>11}{'recall':>9}",
    ]
    for k in KINDS + ["ALL"]:
        if k == "ALL":
            t, f_, n_ = sum(tp.values()), sum(fp.values()), sum(fn.values())
        else:
            t, f_, n_ = tp[k], fp[k], fn[k]
        lines.append(f"{k:<8}{t:>5}{f_:>5}{n_:>5}{ratio(t, t + f_):>11}{ratio(t, t + n_):>9}")
    lines += ["", "FP = detector flagged something that is not a gold item (includes hard negatives).",
              "FN = gold item not flagged. n/a = zero denominator."]
    return "\n".join(lines) + "\n"


def main() -> None:
    r = random.Random(SEED)
    samples = [sample(r) for _ in range(N)]
    OUT.mkdir(exist_ok=True)
    with (OUT / "pii_synth.jsonl").open("w", encoding="utf-8") as f:
        for text, gold in samples:
            f.write(json.dumps({"text": text, "gold": gold}, ensure_ascii=False) + "\n")
    tp, fp, fn = evaluate(samples)
    text = report(tp, fp, fn, N)
    (OUT / "pii_eval.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
