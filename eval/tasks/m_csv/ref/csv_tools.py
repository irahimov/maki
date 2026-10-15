def _split(line: str) -> list[str]:
    fields: list[str] = []
    cur: list[str] = []
    in_quotes = False
    quoted = False
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes
            quoted = True
        elif ch == "," and not in_quotes:
            fields.append(_finish(cur, quoted))
            cur, quoted = [], False
        else:
            cur.append(ch)
    fields.append(_finish(cur, quoted))
    return fields


def _finish(chars: list[str], quoted: bool) -> str:
    value = "".join(chars)
    return value if quoted else value.strip()


def parse_csv(text: str) -> list[dict[str, str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    header = [h.strip() for h in _split(lines[0])]
    rows: list[dict[str, str]] = []
    for ln in lines[1:]:
        fields = _split(ln)
        if len(fields) != len(header):
            raise ValueError("field count mismatch")
        rows.append(dict(zip(header, fields)))
    return rows
