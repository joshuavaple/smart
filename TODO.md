## Base business layer calculations at contract rate
    - [x] Monthly principal + interest payment: calculates the total payment for a loan based on constant payments and a constant interest rate.
    - [x] Amortization schedule: period-by-period split of each payment into principal vs. interest, plus remaining balance.
    - [ ] Gross Debt Service (GDS): (mortgage P&I + property tax + heating + 50% of condo fees) / gross income
    - [ ] TDS (Total Debt Service): GDS + other debt obligations (car loans, credit cards, student loans) / gross income

## Make the tools based on the calculations above
    - [ ] for simplicity, replicate the same docstrings of the functions in @tool-decorated functions for agents
    - [ ] LATER: find a way to reuse the business function docstrings

## Base Ontario market version
    - [ ] Canada-specific monthly payment: modified payment above with semi-annual compound interest, not monthly.
    - [ ] Land Transfer Tax (LTT): provincial LTT and any municipal LTT (e.g., Toronto)
    - [ ] Total closing costs estimation:
        - downpayment
        - LTT (provincial + municipal)
        - legal fees, 
        - title insurance, 
        - home inspection, 
        - CMHC premium if applicable, 
        - adjustments (prepaid property tax/utilities)

## Affordability tests at MQR
    - [ ] Mortgage Stress Test (MQR — Minimum Qualifying Rate): Borrower must qualify at the greater of: contract rate + 2%, or 5.25%.
    - [ ] Gross Debt Service (GDS) using the MQR: (mortgage P&I + property tax + heating + 50% of condo fees) / gross income ≤ 39%
    - [ ] TDS (Total Debt Service) using the MQR: GDS + other debt obligations (car loans, credit cards, student loans) / gross income ≤ 44%
    
## Personal finance context
    - [ ] Income tax: given an annual taxable income and tax brackets, calculate total income tax.
    - [ ] Disposable monthly income after tax and housing commitment


