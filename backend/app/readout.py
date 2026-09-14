"""Plain-English readout for a scenario's results. Deterministic and
template-based (not LLM-generated) so it's reproducible and auditable --
answers the same questions every time from the same numbers: does this
beat buy-and-hold risk-adjusted, how deep/long are the worst drawdowns, how
bad have losing streaks been, and is the edge real or fragile.
"""

from __future__ import annotations


def generate_readout(name: str, kpis: dict, benchmarks: dict[str, dict] | None = None) -> str:
    lines: list[str] = []

    cagr = kpis.get("cagr_pct", 0.0)
    lines.append(
        f"{name}: {cagr:.1f}% CAGR, {kpis.get('total_return_pct', 0.0):.1f}% total return "
        f"over {kpis.get('start_date', '?')} to {kpis.get('end_date', '?')}."
    )

    calmar = kpis.get("calmar_ratio")
    if benchmarks:
        for label, b in benchmarks.items():
            b_cagr = b.get("cagr_pct", 0.0)
            direction = "beat" if cagr > b_cagr else ("trailed" if cagr < b_cagr else "matched")
            sentence = f"That {direction} {label} buy-and-hold ({b_cagr:.1f}% CAGR)"
            b_calmar = b.get("calmar_ratio")
            if calmar is not None and b_calmar is not None:
                risk_direction = "better" if calmar > b_calmar else "worse"
                sentence += f", and was {risk_direction} on a return-per-unit-of-drawdown basis (Calmar {calmar:.2f} vs {b_calmar:.2f})"
            lines.append(sentence + ".")

    max_dd = kpis.get("max_drawdown_pct", 0.0)
    max_dd_days = kpis.get("max_drawdown_days", 0)
    lines.append(f"Max drawdown was {max_dd:.1f}%, lasting up to {max_dd_days} days peak-to-recovery.")

    n_big_dd = kpis.get("num_drawdowns_over_20pct", 0)
    if n_big_dd:
        plural = "s" if n_big_dd != 1 else ""
        lines.append(
            f"There {'were' if n_big_dd != 1 else 'was'} {n_big_dd} drawdown{plural} worse than 20% "
            "in this window -- expect to sit through stretches like that, not just read about them."
        )

    worst_day = kpis.get("worst_day")
    if worst_day:
        lines.append(f"Worst single day: {worst_day['return_pct']:.1f}% on {worst_day['date']}.")

    worst_month = kpis.get("worst_month")
    if worst_month:
        lines.append(
            f"Worst month: {worst_month['return_pct']:.1f}% ({worst_month['year']}-{worst_month['month']:02d})."
        )

    streak = kpis.get("max_consecutive_losses", 0)
    if streak:
        lines.append(
            f"Longest losing streak: {streak} trades in a row, compounding to "
            f"{kpis.get('worst_losing_streak_pct', 0.0):.1f}% -- the stretch that would have tested your nerve most."
        )

    n_trades = kpis.get("num_trades", 0)
    win_rate = kpis.get("win_rate_pct")
    if n_trades and win_rate is not None:
        lines.append(
            f"Win rate was {win_rate:.1f}% across {n_trades} completed trades -- a real "
            "trend-following edge can look exactly like this even when it works (small losses, "
            "occasional big wins)."
        )

    if n_trades and n_trades < 10:
        lines.append(
            f"Only {n_trades} completed trades in this window: treat this result as a fragile, "
            "small-sample signal, not a proven edge."
        )

    return " ".join(lines)
