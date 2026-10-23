"""Indicative mortgage rate estimation from Bank of Canada benchmarks.

fixed    ~ GoC yield (matching term) + spread
variable ~ prime + discount

Benchmarks come from the Bank of Canada Valet API. The spreads are ASSUMPTIONS,
not measured data: calibrate them against real quotes and update SPREADS.
The output is an indicative range, never a lender offer.
"""

import json
from dataclasses import dataclass
from datetime import date
from typing import Callable, Literal
from urllib.request import urlopen

VALET_URL = "https://www.bankofcanada.ca/valet/observations/{series}/json?recent=1"

# Verified against the live Valet API. There is no 1-year series.
YIELD_SERIES = {
    2: "BD.CDN.2YR.DQ.YLD",
    3: "BD.CDN.3YR.DQ.YLD",
    5: "BD.CDN.5YR.DQ.YLD",
    7: "BD.CDN.7YR.DQ.YLD",
    10: "BD.CDN.10YR.DQ.YLD",
}
PRIME_SERIES = "V80691311"  # weekly

# PLACEHOLDER assumptions in percentage points: (low, high). Calibrate these.
SPREADS_AS_OF = "2026-10-22"
FIXED_SPREADS = {
    "insured": (0.8, 1.3),
    "uninsured": (1.2, 1.8),
}
# Variable discount relative to prime (negative = below prime).
VARIABLE_DISCOUNTS = {
    "insured": (-1.0, -0.5),
    "uninsured": (-0.8, -0.2),
}

RateType = Literal["fixed", "variable"]
Fetcher = Callable[[str], tuple[date, float]]


@dataclass(frozen=True)
class RateEstimate:
    rate_type: RateType
    term_years: int
    insured: bool
    benchmark_name: str
    benchmark_pct: float
    benchmark_date: date
    spread_low: float
    spread_high: float
    estimate_low: float
    estimate_high: float
    spreads_as_of: str

    @property
    def midpoint(self) -> float:
        return round((self.estimate_low + self.estimate_high) / 2, 4)

    def as_dict(self) -> dict:
        return {
            "rate_type": self.rate_type,
            "term_years": self.term_years,
            "insured": self.insured,
            "benchmark": {
                "name": self.benchmark_name,
                "value_pct": self.benchmark_pct,
                "as_of": self.benchmark_date.isoformat(),
            },
            "spread_range_pct": [self.spread_low, self.spread_high],
            "estimate_range_pct": [self.estimate_low, self.estimate_high],
            "midpoint_pct": self.midpoint,
            "spreads_as_of": self.spreads_as_of,
            "note": "Indicative only, not a lender offer. Spreads are assumptions.",
        }


def fetch_latest(series: str) -> tuple[date, float]:
    """Return (observation date, value in percent) for the latest Valet observation."""
    with urlopen(VALET_URL.format(series=series), timeout=15) as resp:
        payload = json.load(resp)
    observations = payload.get("observations")
    if not observations:
        raise ValueError(f"No observations returned for series {series}")
    obs = observations[-1]
    return date.fromisoformat(obs["d"]), float(obs[series]["v"])


def estimate_rate(
    term_years: int = 5,
    rate_type: RateType = "fixed",
    insured: bool = True,
    fetch: Fetcher = fetch_latest,
) -> RateEstimate:
    """Estimate an indicative mortgage rate range from current benchmarks.

    Args:
        term_years: Mortgage term. Fixed supports 2, 3, 5, 7, 10. Variable ignores it.
        rate_type: "fixed" (GoC yield + spread) or "variable" (prime + discount).
        insured: True for a high-ratio (insured) mortgage, which prices lower.
        fetch: Injectable data source, so tests need no network.
    """
    tier = "insured" if insured else "uninsured"

    if rate_type == "fixed":
        if term_years not in YIELD_SERIES:
            raise ValueError(
                f"Unsupported term {term_years}; choose from {sorted(YIELD_SERIES)}"
            )
        series = YIELD_SERIES[term_years]
        name = f"GoC {term_years}-year benchmark bond yield"
        low, high = FIXED_SPREADS[tier]
    elif rate_type == "variable":
        series = PRIME_SERIES
        name = "Prime rate"
        low, high = VARIABLE_DISCOUNTS[tier]
    else:
        raise ValueError(f"rate_type must be 'fixed' or 'variable', got {rate_type!r}")

    obs_date, benchmark = fetch(series)
    return RateEstimate(
        rate_type=rate_type,
        term_years=term_years,
        insured=insured,
        benchmark_name=name,
        benchmark_pct=benchmark,
        benchmark_date=obs_date,
        spread_low=low,
        spread_high=high,
        estimate_low=round(benchmark + low, 4),
        estimate_high=round(benchmark + high, 4),
        spreads_as_of=SPREADS_AS_OF,
    )


if __name__ == "__main__":
    for kwargs in (
        {"rate_type": "fixed", "term_years": 5, "insured": True},
        {"rate_type": "fixed", "term_years": 5, "insured": False},
        {"rate_type": "variable", "insured": True},
    ):
        print(json.dumps(estimate_rate(**kwargs).as_dict(), indent=2))
