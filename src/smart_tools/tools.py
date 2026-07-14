from finance.calculations import _pmt, _amortization_schedule, _property_tax_amount
from finance.websearch import (
    _fetch_link_content, 
    CANADA_PROPERTY_TAX_RATE_URL, 
    CANADA_PROPERTY_TAX_RATE_DEFAULT)
from langchain.tools import tool
from typing import Union
import pandas as pd


@tool
def pmt(rate:float, nper: int, pv: Union[float, int], fv=0, when=0):
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
def amortization_schedule(principal, annual_rate, nper, periods_per_year=12, fv=0, when=0) -> pd.DataFrame:
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
    return _amortization_schedule(principal, annual_rate, nper, periods_per_year, fv, when)

@tool
def fetch_canada_property_tax_rate():
    """
    Searches online for the updated property tax rate by major city in Canada.

    Returns:
        A markdown text listing tax rates of Canada's major cities.
    """
    return _fetch_link_content(CANADA_PROPERTY_TAX_RATE_URL)

@tool
def default_canada_property_tax_rate():
    """
    Returns an estimated conservatively high property tax rate when the online search result does not include the city needed.
    """
    return f"Estimated property tax rate (conservatively): {CANADA_PROPERTY_TAX_RATE_DEFAULT*100}%"

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