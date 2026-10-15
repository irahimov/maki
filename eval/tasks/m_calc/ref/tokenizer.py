import re

NUMBER = re.compile(r"\d+(?:\.\d+)?")


def tokenize(expr: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(expr):
        ch = expr[pos]
        if ch.isspace():
            pos += 1
            continue
        m = NUMBER.match(expr, pos)
        if m:
            tokens.append(m.group())
            pos = m.end()
        elif ch in "+-*/()":
            tokens.append(ch)
            pos += 1
        else:
            raise ValueError(f"bad character {ch!r}")
    return tokens
