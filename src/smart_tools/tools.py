from typing import Union
from langchain.tools import tool


@tool
def pmt(rate:float, nper: int, pv: Union[float, int], fv=0, when=0):
    """
    Replicates Excel's PMT function, calculates the payment for a loan based on constant payments and a constant interest rate.

    rate : interest rate per period
    nper : total number of payment periods
    pv   : present value (loan amount, positive if borrowed)
    fv   : future value (balance after last payment), default 0
    when : 0 = payments at end of period (ordinary annuity, default)
           1 = payments at start of period (annuity due)

    Returns the payment per period (negative = cash outflow, matching Excel's sign convention).
    """
    if rate == 0:
        return -(pv + fv) / nper

    factor = (1 + rate) ** nper
    return -(rate * (fv + pv * factor)) / ((1 + rate * when) * (factor - 1))