"""MCP server exposing mortgage-customer tools that sit outside the agent's calculations.

Run with: python -m mcp_server.server   (stdio transport)
Do not print to stdout: with stdio it carries the protocol. Use logging (stderr).
"""

import logging
from typing import Literal
from urllib.error import URLError

from mcp.server.fastmcp import FastMCP

from mcp_server.rate_estimation import estimate_rate

logger = logging.getLogger(__name__)

mcp = FastMCP("smart-rate-estimation")


@mcp.tool()
def estimate_mortgage_rate(
    rate_type: Literal["fixed", "variable"] = "fixed",
    term_years: Literal[2, 3, 5, 7, 10] = 5,
    insured: bool = True,
) -> dict:
    """Estimate an indicative Canadian mortgage rate range from current benchmarks.

    Fixed rates are estimated as the Government of Canada bond yield for the
    matching term plus a typical lender spread. Variable rates are estimated as
    the prime rate plus a typical discount. Benchmarks come live from the Bank
    of Canada.

    The result is an INDICATIVE RANGE, not a lender offer. The spreads are
    assumptions that vary by lender, credit profile and promotions. Always
    present the range with its benchmark and date, and let the user override it.

    Args:
        rate_type: "fixed" (priced off the GoC bond yield) or "variable"
            (priced off prime).
        term_years: Mortgage term in years. Only used for fixed; variable
            ignores it.
        insured: True if the down payment is under 20% (high-ratio, CMHC or
            similar insurance), which prices lower. False for conventional.

    Returns:
        A dict with the benchmark (name, value_pct, as_of), the assumed spread
        range, estimate_range_pct [low, high], midpoint_pct, spreads_as_of and
        a note. All rates are percentages, for example 4.5 means 4.5%.
    """
    try:
        return estimate_rate(term_years, rate_type, insured).as_dict()
    except (URLError, TimeoutError) as exc:
        logger.error("Bank of Canada request failed: %s", exc)
        raise RuntimeError(
            "Bank of Canada rate data is temporarily unavailable. "
            "Ask the user for a rate instead."
        ) from exc


if __name__ == "__main__":
    mcp.run(transport="stdio")
