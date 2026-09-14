"""Plain-English explanation of today's signal for the daily log: why it's
what it is, and what would need to happen for it to change. Deterministic
templates, not LLM-generated -- same inputs always produce the same text.
"""

from __future__ import annotations

from . import config


def explain_signal(close: float, ma_fast: float | None, ma_slow: float | None, weight: float) -> str:
    if ma_fast is None or ma_slow is None:
        return "Not enough price history yet for both moving averages -- defaulting to cash."
    if weight > 0:
        return (
            f"^NDX ({close:.2f}) is above both its {config.MA_FAST}d MA ({ma_fast:.2f}) and "
            f"{config.MA_SLOW}d MA ({ma_slow:.2f}) -- trend up, hold {config.LONG_TICKER}."
        )
    if weight < 0:
        return (
            f"^NDX ({close:.2f}) is below both its {config.MA_FAST}d MA ({ma_fast:.2f}) and "
            f"{config.MA_SLOW}d MA ({ma_slow:.2f}) -- trend down, hold {config.SHORT_TICKER}."
        )
    return (
        f"^NDX ({close:.2f}) is mixed relative to its {config.MA_FAST}d MA ({ma_fast:.2f}) and "
        f"{config.MA_SLOW}d MA ({ma_slow:.2f}) -- neither clearly above nor below both, hold cash."
    )


def next_exit_trigger(
    ma_fast: float | None,
    ma_slow: float | None,
    fast_ma_short: float | None,
    weight: float,
) -> str | None:
    """Describes what would flip today's signal -- Job 1's own flip level,
    plus the Job 3 rules that don't require knowing your own entry price
    (fast trend-break, mean-reversion extension). Stop-loss isn't included:
    it depends on your actual entry price, which this live signal snapshot
    doesn't track."""
    if weight == 0 or ma_fast is None or ma_slow is None:
        return None

    extension_pct = config.EXIT_EXTENSION_PCT
    if weight > 0:
        conditions = [f"closes back below its {config.MA_FAST}d MA (${ma_fast:.2f}) or {config.MA_SLOW}d MA (${ma_slow:.2f})"]
        if fast_ma_short is not None:
            conditions.append(f"closes below the faster {config.EXIT_FAST_MA_PERIOD}d MA (${fast_ma_short:.2f})")
        conditions.append(f"stretches more than {extension_pct * 100:.0f}% above the {config.MA_FAST}d MA (above ${ma_fast * (1 + extension_pct):.2f})")
    else:
        conditions = [f"closes back above its {config.MA_FAST}d MA (${ma_fast:.2f}) or {config.MA_SLOW}d MA (${ma_slow:.2f})"]
        if fast_ma_short is not None:
            conditions.append(f"closes above the faster {config.EXIT_FAST_MA_PERIOD}d MA (${fast_ma_short:.2f})")
        conditions.append(f"stretches more than {extension_pct * 100:.0f}% below the {config.MA_FAST}d MA (below ${ma_fast * (1 - extension_pct):.2f})")

    joined = "; or if ^NDX ".join(conditions)
    return (
        f"Would exit if ^NDX {joined}. (A stop-loss would also apply once you know your own "
        "entry price -- this live snapshot doesn't track a live position.)"
    )
