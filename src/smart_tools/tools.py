from finance.calculations import (
    _pmt,
    _amortization_schedule,
    _property_tax_amount,
    _gross_debt_service,
)
from finance.websearch import _fetch_link_content, CANADA_PROPERTY_TAX_RATE_URL
from finance.estimations import CANADA_PROPERTY_TAX_RATE, CANADA_TORONTO_UTILITIES
from langchain.tools import tool
from typing import Union, Optional
import pandas as pd
import uuid
from pathlib import Path
from core.storage import ArtifactStore
from core.config import settings
from core.storage import get_store
from pydantic import BaseModel, Field


# session/process-scoped cache mapping artifact_id -> computed DataFrame
_DF_CACHE: dict[str, pd.DataFrame] = {}

# resolved once at import time from Settings; swap backend via STORAGE_BACKEND in .env
_store = get_store(settings)

@tool
def pmt(rate: float, nper: int, pv: Union[float, int], fv=0, when=0):
    """Replicates Excel's PMT function, calculates the payment for a loan based on constant payments and a constant interest rate.

    Args:
        rate: Interest rate per period.
        nper: Total number of payment periods.
        pv: Present value (loan amount, positive if borrowed).
        fv: Future value (balance after last payment), default 0.
        when: 0 = payments at end of period (ordinary annuity, default),
            1 = payments at start of period (annuity due).

    Returns:
        The payment per period (negative = cash outflow, matching Excel's sign convention).
    """
    return _pmt(rate, nper, pv, fv, when)


@tool
def amortization_schedule(
    principal, annual_rate, nper, periods_per_year=12, fv=0, when=0
) -> pd.DataFrame:
    """Build a period-by-period amortization schedule.

    Args:
        principal: Loan amount (positive).
        annual_rate: Nominal annual interest rate (e.g. 0.06 for 6%).
        nper: Total number of payment periods.
        periods_per_year: Compounding/payment frequency (12 = monthly).
        fv: Target balance at the end (0 for fully amortizing).
        when: 0 = end-of-period payments, 1 = start-of-period.

    Returns:
        A DataFrame indexed by period, with columns: payment, principal_paid,
        interest_paid, ending_balance.
    """

    df = _amortization_schedule(
        principal, annual_rate, nper, periods_per_year, fv, when
    )
    artifact_id = uuid.uuid4().hex[:8]
    _DF_CACHE[artifact_id] = df
    preview = pd.concat([df.head(3), df.tail(3)])
    return (
        f"artifact_id: {artifact_id}\n"
        f"{preview.to_string(index=False)}\n"
        f"... {len(df)} periods total. Use export_dataframe(artifact_id) to save full CSV."
    )

class ExportDataframeInput(BaseModel):
    artifact_id: str = Field(description="The ID of the file")
    filename: Optional[str] = Field(
        default=None,
        description="Optional concise filename for the CSV, limit to 1-2 words separated by underscore."
        "Defaults to '<task>_<artifact_id>.csv' if omitted where <task> is inferred from the conversation with the user, e.g., amortization, income_tax...",
    )

@tool("export_dataframe", args_schema=ExportDataframeInput)
def export_dataframe(artifact_id: str, filename: Optional[str] = None) -> str:
    """Export a previously computed DataFrame (by artifact_id) to CSV.

    Only call this after the user has explicitly confirmed they want the
    full data exported — do not export automatically after every
    tool call.

    Args:
        artifact_id: The id returned by a tool.
        filename: Optional output filename; a default is generated if omitted.

    Returns:
        The path (or URI) where the CSV was written, or an error message
        if the artifact_id is unknown.
    """
    df = _DF_CACHE.get(artifact_id)
    if df is None:
        return (
            f"error: no cached data found for id '{artifact_id}'. "
            f"It may have expired or never existed — recompute with your tool."
        )

    safe_name = f"{Path(filename).name}_{artifact_id}" if filename else f"file_{artifact_id}.csv"
    if not safe_name.endswith(".csv"):
        safe_name += ".csv"

    path = _store.write_csv(df, safe_name)
    return f"Exported {len(df)} rows to: {path}"


@tool
def fetch_canada_property_tax_rate():
    """
    Searches online for the updated property tax rate by major city in Canada.

    Returns:
        A markdown text listing tax rates of Canada's major cities.
    """
    return _fetch_link_content(CANADA_PROPERTY_TAX_RATE_URL)


@tool
def estimate_canada_property_tax_rate():
    """
    Returns an estimated conservatively high property tax rate when the online search result does not include the city needed.
    """
    return (
        f"Estimated property tax rate (conservatively): {CANADA_PROPERTY_TAX_RATE*100}%"
    )


@tool
def property_tax_amount(
    rate: Union[float, int], assessed_value: Union[float, int]
) -> float:
    """Calculate the property tax amount of a home based on its assessed value.
    Args:
        rate: Property tax rate.
        assessed_value: Assessed value of the home.

    Returns:
        The property tax amount.
    """
    return _property_tax_amount(rate, assessed_value)


@tool
def estimate_canada_utilities_amount():
    """
    Returns an estimated utilities expenses for each property type in Toronto, used as the proxy for Canada.
    """
    return CANADA_TORONTO_UTILITIES


@tool
def gross_debt_service(
    mortgage_pmt, property_tax, utilities, other_expenses, gross_income
) -> float:
    """
    Calculate the gross debt service ratio (GDS) of a household in a period (e.g., monthly).

    Args:
        mortgage_pmt: total mortgage payment in the period (principal and interest)
        property_tax: proprety tax amount in the period
        utilities: utilities amount in the period
        other_expenses: other household expenses like phone, internet and cable in the period
        gross_income: household income before tax in the period
    
    Returns:
        The GDS ratio
    """
    return _gross_debt_service(
        mortgage_pmt, property_tax, utilities, other_expenses, gross_income
    )


