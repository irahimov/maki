import pii_masker as pm

IBAN = pm.build_iban("NABZ", "0000000013701000" + "1944")
CARD_BODY = "411111111111111"
CARD = CARD_BODY + pm.luhn_check_digit(CARD_BODY)


def kinds(text):
    return [h.kind for h in pm.find(text)]


def test_iban_helper_is_valid():
    assert pm.iban_ok(IBAN)
    assert len(IBAN) == 28 and IBAN.startswith("AZ")


def test_iban_detected_compact_and_spaced():
    assert kinds(f"hesab {IBAN} ok") == ["iban"]
    spaced = " ".join(IBAN[i:i + 4] for i in range(0, 28, 4))
    assert kinds(f"hesab {spaced} ok") == ["iban"]


def test_iban_wrong_checksum_not_detected():
    bad = IBAN[:4] + ("0" if IBAN[4] != "0" else "1") + IBAN[5:]
    assert not pm.iban_ok(bad)
    assert kinds(bad) == []


def test_card_luhn_valid_detected_with_separators():
    assert kinds(f"kart {CARD}") == ["card"]
    spaced = " ".join(CARD[i:i + 4] for i in range(0, 16, 4))
    assert kinds(spaced) == ["card"]
    dashed = "-".join(CARD[i:i + 4] for i in range(0, 16, 4))
    assert kinds(dashed) == ["card"]


def test_card_luhn_invalid_not_detected():
    bad = CARD_BODY + str((int(pm.luhn_check_digit(CARD_BODY)) + 1) % 10)
    assert kinds(bad) == []


def test_email_detected():
    assert kinds("yaz: ali.v@bank.az sonra") == ["email"]


def test_phone_formats():
    assert kinds("+994 50 123 45 67") == ["phone"]
    assert kinds("0501234567") == ["phone"]
    assert kinds("050-123-45-67") == ["phone"]


def test_fin_requires_context():
    assert kinds("FIN: AB12345") == ["fin"]
    assert kinds("kod AB12345 var") == []


def test_plain_numbers_not_detected():
    assert kinds("məbləğ 1000 AZN, tarix 2026-10-18") == []


def test_mask_keeps_last_four_characters():
    masked, _ = pm.mask(f"kart {CARD}")
    assert masked == "kart " + "*" * 12 + CARD[-4:]


def test_mask_iban_keeps_spaces_and_last_four():
    spaced = " ".join(IBAN[i:i + 4] for i in range(0, 28, 4))
    masked, _ = pm.mask(spaced)
    assert masked.count("*") == 28 - 4 and masked.endswith(IBAN[-4:])
    assert masked.count(" ") == 6


def test_mask_email():
    masked, hits = pm.mask("ali.v@bank.az")
    assert [h.kind for h in hits] == ["email"]
    assert masked == "*" * (len("ali.v@bank.az") - 4) + "k.az"


def test_mask_leaves_text_without_pii_unchanged():
    text = "Bu normal bir cümlədir, 12 manat."
    assert pm.mask(text) == (text, [])
