from app.rationale import explain_signal, next_exit_trigger


def test_explain_signal_long():
    text = explain_signal(close=110.0, ma_fast=100.0, ma_slow=90.0, weight=1.0)
    assert "TQQQ" in text
    assert "110.00" in text


def test_explain_signal_short():
    text = explain_signal(close=80.0, ma_fast=100.0, ma_slow=110.0, weight=-1.0)
    assert "SQQQ" in text


def test_explain_signal_cash():
    text = explain_signal(close=95.0, ma_fast=100.0, ma_slow=90.0, weight=0.0)
    assert "cash" in text.lower()


def test_explain_signal_warmup():
    text = explain_signal(close=95.0, ma_fast=None, ma_slow=None, weight=0.0)
    assert "not enough" in text.lower()


def test_next_exit_trigger_none_when_cash():
    assert next_exit_trigger(ma_fast=100.0, ma_slow=90.0, fast_ma_short=105.0, weight=0.0) is None


def test_next_exit_trigger_none_when_warmup():
    assert next_exit_trigger(ma_fast=None, ma_slow=None, fast_ma_short=None, weight=1.0) is None


def test_next_exit_trigger_long_mentions_relevant_levels():
    text = next_exit_trigger(ma_fast=100.0, ma_slow=90.0, fast_ma_short=105.0, weight=1.0)
    assert text is not None
    assert "$100.00" in text
    assert "$90.00" in text
    assert "$105.00" in text
    assert "stop-loss" in text.lower()


def test_next_exit_trigger_short_mentions_relevant_levels():
    text = next_exit_trigger(ma_fast=100.0, ma_slow=110.0, fast_ma_short=95.0, weight=-1.0)
    assert text is not None
    assert "above" in text.lower()


def test_next_exit_trigger_handles_missing_fast_ma():
    text = next_exit_trigger(ma_fast=100.0, ma_slow=90.0, fast_ma_short=None, weight=1.0)
    assert text is not None
    assert "faster" not in text.lower()
