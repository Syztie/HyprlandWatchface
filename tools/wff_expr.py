"""Evaluator for Watch Face Format arithmetic expressions.

Covers the operators and functions documented at
https://developer.android.com/reference/wear-os/wff/common/attributes/arithmetic-expression
that this watch face uses. Used by the preview renderer and the audits to
check expressions offline, for example the ISO week formula.
"""
import math
import re

TOKEN = re.compile(r"""
    \s*(?:
      (?P<num>\d+\.\d*|\.\d+|\d+)
    | (?P<str>"[^"]*")
    | (?P<src>\[[A-Za-z0-9_.]+\])
    | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<op>&&|\|\||==|!=|<=|>=|[-+*/%<>!?:(),~&|])
    )""", re.X)

BINARY = {
    "||": 1, "&&": 2, "|": 3, "&": 4, "==": 5, "!=": 5,
    "<": 6, "<=": 6, ">": 6, ">=": 6, "+": 7, "-": 7, "*": 8, "/": 8, "%": 8,
}


def tokenize(text):
    pos, out = 0, []
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise SyntaxError(f"bad token at {text[pos:]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def number_format(pattern, value):
    # Subset of java.text.DecimalFormat: "0", "00", "0.0", "#", "#,###".
    decimals = len(pattern.split(".")[1]) if "." in pattern else 0
    int_part = pattern.split(".")[0]
    min_int = int_part.count("0")
    grouping = "," in int_part
    v = round(float(value), decimals)
    text = f"{abs(v):,.{decimals}f}" if grouping else f"{abs(v):.{decimals}f}"
    head = text.split(".")[0]
    if len(head.replace(",", "")) < min_int:
        text = "0" * (min_int - len(head)) + text
    return ("-" if v < 0 else "") + text


FUNCTIONS = {
    "round": lambda x: math.floor(float(x) + 0.5),
    "floor": lambda x: math.floor(float(x)),
    "ceil": lambda x: math.ceil(float(x)),
    "abs": lambda x: abs(float(x)),
    "fract": lambda x: float(x) - math.floor(float(x)),
    "clamp": lambda x, lo, hi: max(float(lo), min(float(hi), float(x))),
    "max": lambda a, b: max(float(a), float(b)),
    "min": lambda a, b: min(float(a), float(b)),
    "numberFormat": number_format,
    "textLength": lambda s: len(str(s)),
    "subText": lambda s, a, b: str(s)[int(a):int(b)],
}


class Parser:
    def __init__(self, tokens, ctx):
        self.t = tokens
        self.i = 0
        self.ctx = ctx

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, value=None):
        tok = self.peek()
        if value is not None and tok[1] != value:
            raise SyntaxError(f"expected {value!r}, got {tok[1]!r}")
        self.i += 1
        return tok

    def expr(self):
        cond = self.binary(1)
        if self.peek()[1] == "?":
            self.take("?")
            a = self.expr()
            self.take(":")
            b = self.expr()
            return a if truthy(cond) else b
        return cond

    def binary(self, min_prec):
        left = self.unary()
        while True:
            op = self.peek()[1]
            prec = BINARY.get(op)
            if self.peek()[0] != "op" or prec is None or prec < min_prec:
                return left
            self.take()
            right = self.binary(prec + 1)
            left = apply(op, left, right)

    def unary(self):
        kind, val = self.peek()
        if kind == "op" and val in "!-~":
            self.take()
            v = self.unary()
            return (not truthy(v)) if val == "!" else (-num(v) if val == "-" else ~int(num(v)))
        return self.primary()

    def primary(self):
        kind, val = self.take()
        if kind == "num":
            return float(val)
        if kind == "str":
            return val[1:-1]
        if kind == "src":
            return self.ctx.lookup(val[1:-1])
        if kind == "id" and val == "null":
            return None
        if kind == "id":
            self.take("(")
            args = []
            if self.peek()[1] != ")":
                args.append(self.expr())
                while self.peek()[1] == ",":
                    self.take(",")
                    args.append(self.expr())
            self.take(")")
            return FUNCTIONS[val](*args)
        if val == "(":
            v = self.expr()
            self.take(")")
            return v
        raise SyntaxError(f"unexpected {val!r}")


def num(v):
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if v is None:
        return 0.0
    return float(v)


def truthy(v):
    if isinstance(v, str):
        return v not in ("", "0", "FALSE", "false")
    return num(v) != 0


def apply(op, a, b):
    if op == "&&":
        return truthy(a) and truthy(b)
    if op == "||":
        return truthy(a) or truthy(b)
    if op in ("==", "!="):
        if a is None or b is None:
            eq = a is b
        elif isinstance(a, str) or isinstance(b, str):
            eq = str(a) == str(b)
        else:
            eq = num(a) == num(b)
        return eq if op == "==" else not eq
    a, b = num(a), num(b)
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return 0.0 if b == 0 else a / b
    if op == "%":
        return 0.0 if b == 0 else math.fmod(a, b)
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    if op == "&":
        return float(int(a) & int(b))
    if op == "|":
        return float(int(a) | int(b))
    raise SyntaxError(op)


def evaluate(text, ctx):
    p = Parser(tokenize(text), ctx)
    v = p.expr()
    if p.i != len(p.t):
        raise SyntaxError(f"trailing tokens in {text!r}")
    return v


def format_template(template, values):
    """printf-style formatting as used by <Template>."""
    out, vi = [], 0
    for m in re.finditer(r"%(%|[-0-9.]*[sd]|[-0-9.]*f)|[^%]+", template):
        tok = m.group(0)
        if not tok.startswith("%"):
            out.append(tok)
        elif tok == "%%":
            out.append("%")
        else:
            v = values[vi]
            vi += 1
            if tok.endswith("d"):
                v = int(num(v))
            elif tok.endswith("s") and isinstance(v, float) and v.is_integer():
                v = int(v)
            out.append(tok % v)
    return "".join(out)
