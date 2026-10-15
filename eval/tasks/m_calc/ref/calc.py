from tokenizer import tokenize


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.t = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end")
        self.i += 1
        return tok

    def expr(self) -> float:
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def term(self) -> float:
        value = self.factor()
        while self.peek() in ("*", "/"):
            op = self.take()
            rhs = self.factor()
            if op == "*":
                value *= rhs
            else:
                if rhs == 0:
                    raise ZeroDivisionError("division by zero")
                value /= rhs
        return value

    def factor(self) -> float:
        tok = self.take()
        if tok == "-":
            return -self.factor()
        if tok == "(":
            value = self.expr()
            if self.take() != ")":
                raise ValueError("expected )")
            return value
        if tok in ("+", "*", "/", ")"):
            raise ValueError(f"unexpected {tok}")
        return float(tok)


def evaluate(expr: str) -> float:
    tokens = tokenize(expr)
    if not tokens:
        raise ValueError("empty expression")
    parser = _Parser(tokens)
    value = parser.expr()
    if parser.peek() is not None:
        raise ValueError(f"unexpected {parser.peek()}")
    return value
