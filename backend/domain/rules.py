"""Pure rules: no framework or persistence dependencies."""

from decimal import ROUND_HALF_EVEN, Decimal


class BusinessError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


TRANSITIONS = {
    "merchant": {
        "pending": {"accepted", "rejected"},
        "accepted": {"preparing", "cancelled"},
        "preparing": {"ready"},
        "ready": {"fulfilled"},
    },
    "delivery": {
        "unassigned": {"offered", "cancelled"},
        "offered": {"assigned", "unassigned"},
        "assigned": {"picked_up", "failed"},
        "picked_up": {"delivered", "failed"},
    },
}


def transition(kind: str, previous: str, target: str) -> None:
    if target not in TRANSITIONS.get(kind, {}).get(previous, set()):
        raise BusinessError("invalid_transition", f"Cannot move {previous} to {target}")


def money(value: Decimal, scale: int) -> Decimal:
    if not value.is_finite() or scale not in range(5):
        raise BusinessError("invalid_money", "Invalid money or currency scale", 422)
    return value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_EVEN)


def balanced(lines: list[tuple[str, Decimal]]) -> None:
    if len(lines) < 2 or any(amount == 0 or not amount.is_finite() for _, amount in lines):
        raise BusinessError("invalid_journal", "A journal requires at least two nonzero lines", 422)
    currencies = {currency for currency, _ in lines}
    if any(sum((v for c, v in lines if c == currency), Decimal(0)) != 0 for currency in currencies):
        raise BusinessError(
            "unbalanced_journal", "Journal must balance independently by currency", 422
        )
