from datetime import date

import pytest

from rate_estimation import PRIME_SERIES, YIELD_SERIES, estimate_rate


def fake_fetch(values):
    calls = []

    def _fetch(series):
        calls.append(series)
        return date(2026, 10, 21), values[series]

    _fetch.calls = calls
    return _fetch


def test_fixed_insured_5y():
    fetch = fake_fetch({YIELD_SERIES[5]: 3.62})
    est = estimate_rate(5, "fixed", insured=True, fetch=fetch)
    assert fetch.calls == [YIELD_SERIES[5]]
    assert (est.estimate_low, est.estimate_high) == (4.42, 4.92)
    assert est.midpoint == 4.67


def test_fixed_uninsured_is_higher_than_insured():
    fetch = fake_fetch({YIELD_SERIES[5]: 3.62})
    insured = estimate_rate(5, "fixed", True, fetch)
    uninsured = estimate_rate(5, "fixed", False, fetch)
    assert uninsured.estimate_low > insured.estimate_low
    assert uninsured.estimate_high > insured.estimate_high


def test_term_selects_matching_yield_series():
    fetch = fake_fetch({YIELD_SERIES[3]: 3.43})
    estimate_rate(3, "fixed", fetch=fetch)
    assert fetch.calls == [YIELD_SERIES[3]]


def test_variable_uses_prime_with_negative_discount():
    fetch = fake_fetch({PRIME_SERIES: 4.45})
    est = estimate_rate(rate_type="variable", insured=True, fetch=fetch)
    assert fetch.calls == [PRIME_SERIES]
    assert (est.estimate_low, est.estimate_high) == (3.45, 3.95)


def test_unsupported_term_raises_before_fetching():
    fetch = fake_fetch({})
    with pytest.raises(ValueError, match="Unsupported term"):
        estimate_rate(1, "fixed", fetch=fetch)
    assert fetch.calls == []


def test_invalid_rate_type():
    with pytest.raises(ValueError, match="rate_type"):
        estimate_rate(5, "hybrid", fetch=fake_fetch({}))  # type: ignore[arg-type]


def test_as_dict_is_explainable():
    est = estimate_rate(5, "fixed", fetch=fake_fetch({YIELD_SERIES[5]: 3.62}))
    d = est.as_dict()
    assert d["benchmark"] == {
        "name": "GoC 5-year benchmark bond yield",
        "value_pct": 3.62,
        "as_of": "2026-10-21",
    }
    assert d["estimate_range_pct"] == [4.42, 4.92]
    assert "not a lender offer" in d["note"]
