"""Glossary data: structured entries for financial metrics and terms.

Auto-populates 'short' descriptions from definitions.py and info_analysis.py,
then enriches key metrics with detailed explanations, examples, and formulas.
"""

from fundascope.core.model import METRIC_DEFINITIONS, KEY_METRICS
from fundascope.core.info_api import METRIC_TOOLTIPS

# ---------------------------------------------------------------------------
# Category mappings
# ---------------------------------------------------------------------------

# Map definition keys to categories based on their position in definitions.py
_INCOME_STMT_KEYS = {
    "Total Revenue", "Operating Revenue", "Cost Of Revenue", "Gross Profit",
    "Operating Expense", "Selling General And Administration",
    "Research And Development",
    "Depreciation And Amortization In Income Statement",
    "Depreciation Income Statement", "Other Operating Expenses",
    "Operating Income", "Total Operating Income As Reported",
    "Net Non Operating Interest Income Expense",
    "Interest Income Non Operating", "Interest Expense Non Operating",
    "Total Other Finance Cost", "Net Interest Income", "Interest Income",
    "Interest Expense", "Other Income Expense",
    "Other Non Operating Income Expenses", "Special Income Charges",
    "Other Special Charges", "Write Off", "Impairment Of Capital Assets",
    "Restructuring And Mergern Acquisition", "Pretax Income", "Tax Provision",
    "Net Income Continuous Operations", "Net Income Discontinuous Operations",
    "Net Income Including Noncontrolling Interests", "Minority Interests",
    "Net Income", "Net Income From Continuing And Discontinued Operation",
    "Net Income From Continuing Operation Net Minority Interest",
    "Net Income Common Stockholders",
    "Diluted NI Availto Com Stockholders",
    "Otherunder Preferred Stock Dividend", "Basic EPS", "Diluted EPS",
    "Basic Average Shares", "Diluted Average Shares", "Total Expenses",
    "EBIT", "EBITDA", "Normalized EBITDA", "Normalized Income",
    "Reconciled Cost Of Revenue", "Reconciled Depreciation",
    "Total Unusual Items", "Total Unusual Items Excluding Goodwill",
    "Tax Effect Of Unusual Items", "Tax Rate For Calcs",
}

_BALANCE_SHEET_KEYS = {
    "Total Assets", "Current Assets", "Cash And Cash Equivalents",
    "Cash Cash Equivalents And Short Term Investments", "Cash Equivalents",
    "Cash Financial", "Other Short Term Investments", "Accounts Receivable",
    "Receivables", "Other Receivables", "Gross Accounts Receivable",
    "Allowance For Doubtful Accounts Receivable", "Inventory", "Raw Materials",
    "Work In Process", "Finished Goods", "Other Inventories", "Prepaid Assets",
    "Other Current Assets", "Hedging Assets Current",
    "Assets Held For Sale Current", "Total Non Current Assets", "Net PPE",
    "Gross PPE", "Land And Improvements", "Buildings And Improvements",
    "Machinery Furniture Equipment", "Construction In Progress", "Leases",
    "Other Properties", "Properties", "Accumulated Depreciation", "Goodwill",
    "Goodwill And Other Intangible Assets", "Other Intangible Assets",
    "Investments And Advances", "Long Term Equity Investment",
    "Investmentin Financial Assets", "Available For Sale Securities",
    "Held To Maturity Securities", "Trading Securities",
    "Investment Properties", "Non Current Accounts Receivable",
    "Non Current Note Receivables", "Non Current Deferred Assets",
    "Non Current Deferred Taxes Assets", "Defined Pension Benefit",
    "Other Non Current Assets",
    "Total Liabilities Net Minority Interest", "Current Liabilities",
    "Accounts Payable", "Payables", "Payables And Accrued Expenses",
    "Total Tax Payable", "Income Tax Payable", "Current Debt",
    "Current Debt And Capital Lease Obligation",
    "Current Capital Lease Obligation", "Current Deferred Liabilities",
    "Current Deferred Revenue", "Current Accrued Expenses",
    "Dividends Payable",
    "Pension And Other Post Retirement Benefit Plans Current",
    "Other Current Liabilities",
    "Total Non Current Liabilities Net Minority Interest", "Long Term Debt",
    "Long Term Debt And Capital Lease Obligation",
    "Long Term Capital Lease Obligation", "Long Term Provisions",
    "Non Current Deferred Liabilities", "Non Current Deferred Revenue",
    "Non Current Deferred Taxes Liabilities",
    "Non Current Pension And Other Postretirement Benefit Plans",
    "Tradeand Other Payables Non Current", "Other Non Current Liabilities",
    "Total Debt", "Net Debt", "Stockholders Equity", "Common Stock Equity",
    "Capital Stock", "Common Stock", "Preferred Stock",
    "Additional Paid In Capital", "Retained Earnings",
    "Treasury Shares Number", "Treasury Stock",
    "Gains Losses Not Affecting Retained Earnings",
    "Other Equity Adjustments", "Minority Interest",
    "Total Equity Gross Minority Interest", "Total Capitalization",
    "Share Issued", "Ordinary Shares Number", "Tangible Book Value",
    "Working Capital", "Invested Capital", "Net Tangible Assets",
}

_CASHFLOW_KEYS = {
    "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
    "Net Income From Continuing Operations", "Depreciation And Amortization",
    "Depreciation Amortization Depletion", "Deferred Tax",
    "Deferred Income Tax", "Stock Based Compensation",
    "Other Non Cash Items", "Change In Working Capital",
    "Change In Receivables", "Changes In Account Receivables",
    "Change In Inventory", "Change In Payables And Accrued Expense",
    "Change In Payable", "Change In Account Payable",
    "Change In Accrued Expense", "Change In Tax Payable",
    "Change In Income Tax", "Change In Prepaid Assets",
    "Change In Other Working Capital", "Change In Other Current Assets",
    "Change In Other Current Liabilities",
    "Provisionand Write Offof Assets", "Asset Impairment Charge",
    "Gain Loss On Sale Of Business", "Gain Loss On Investment Securities",
    "Net Foreign Currency Exchange Gain Loss",
    "Earnings Losses From Equity Investments",
    "Pension And Employee Benefit Expense", "Operating Gains Losses",
    "Investing Cash Flow", "Cash Flow From Continuing Investing Activities",
    "Capital Expenditure", "Net Business Purchase And Sale",
    "Purchase Of Business", "Sale Of Business", "Purchase Of Investment",
    "Sale Of Investment", "Net Investment Purchase And Sale",
    "Net PPE Purchase And Sale", "Purchase Of PPE", "Sale Of PPE",
    "Net Intangibles Purchase And Sale", "Purchase Of Intangibles",
    "Sale Of Intangibles", "Net Other Investing Changes",
    "Financing Cash Flow", "Cash Flow From Continuing Financing Activities",
    "Net Issuance Payments Of Debt", "Net Long Term Debt Issuance",
    "Long Term Debt Issuance", "Long Term Debt Payments",
    "Net Short Term Debt Issuance", "Short Term Debt Issuance",
    "Short Term Debt Payments", "Net Common Stock Issuance",
    "Common Stock Issuance", "Common Stock Payments",
    "Net Preferred Stock Issuance", "Preferred Stock Issuance",
    "Preferred Stock Payments", "Proceeds From Stock Option Exercised",
    "Cash Dividends Paid", "Common Stock Dividend Paid",
    "Preferred Stock Dividend Paid", "Net Other Financing Charges",
    "Issuance Of Capital Stock", "Repurchase Of Capital Stock",
    "Issuance Of Debt", "Repayment Of Debt", "Free Cash Flow",
    "Changes In Cash", "Effect Of Exchange Rate Changes",
    "Beginning Cash Position", "End Cash Position",
    "Capital Expenditure Reported",
}

# info_analysis.py metric categories
_INFO_CATEGORIES = {
    "marketCap": "Valuation", "trailingPE": "Valuation",
    "forwardPE": "Valuation", "pegRatio": "Valuation",
    "priceToBook": "Valuation",
    "priceToSalesTrailing12Months": "Valuation",
    "enterpriseToEbitda": "Valuation", "enterpriseToRevenue": "Valuation",
    "profitMargins": "Profitability", "operatingMargins": "Profitability",
    "grossMargins": "Profitability", "ebitdaMargins": "Profitability",
    "returnOnEquity": "Profitability", "returnOnAssets": "Profitability",
    "currentRatio": "Financial Health", "quickRatio": "Financial Health",
    "debtToEquity": "Financial Health", "totalDebt": "Financial Health",
    "totalCash": "Financial Health",
    "revenueGrowth": "Growth", "earningsGrowth": "Growth",
    "earningsQuarterlyGrowth": "Growth",
    "dividendYield": "Dividends", "dividendRate": "Dividends",
    "payoutRatio": "Dividends", "fiveYearAvgDividendYield": "Dividends",
    "exDividendDate": "Dividends",
    "currentPrice": "Price & Trading", "fiftyTwoWeekHigh": "Price & Trading",
    "fiftyTwoWeekLow": "Price & Trading",
    "fiftyTwoWeekChange": "Price & Trading", "beta": "Price & Trading",
    "fiftyDayAverage": "Price & Trading",
    "twoHundredDayAverage": "Price & Trading",
    "shortName": "Company Profile", "sector": "Company Profile",
    "industry": "Company Profile", "country": "Company Profile",
    "fullTimeEmployees": "Company Profile",
    "longBusinessSummary": "Company Profile",
}

# Display-friendly label mapping for info_analysis keys
_INFO_LABELS = {
    "marketCap": "Market Cap", "trailingPE": "Trailing P/E",
    "forwardPE": "Forward P/E", "pegRatio": "PEG Ratio",
    "priceToBook": "Price to Book",
    "priceToSalesTrailing12Months": "Price to Sales",
    "enterpriseToEbitda": "EV / EBITDA",
    "enterpriseToRevenue": "EV / Revenue",
    "profitMargins": "Profit Margin", "operatingMargins": "Operating Margin",
    "grossMargins": "Gross Margin", "ebitdaMargins": "EBITDA Margin",
    "returnOnEquity": "Return on Equity", "returnOnAssets": "Return on Assets",
    "currentRatio": "Current Ratio", "quickRatio": "Quick Ratio",
    "debtToEquity": "Debt to Equity", "totalDebt": "Total Debt",
    "totalCash": "Total Cash",
    "revenueGrowth": "Revenue Growth", "earningsGrowth": "Earnings Growth",
    "earningsQuarterlyGrowth": "Quarterly Earnings Growth",
    "dividendYield": "Dividend Yield", "dividendRate": "Dividend Rate",
    "payoutRatio": "Payout Ratio",
    "fiveYearAvgDividendYield": "5Y Avg Dividend Yield",
    "exDividendDate": "Ex-Dividend Date",
    "currentPrice": "Current Price", "fiftyTwoWeekHigh": "52-Week High",
    "fiftyTwoWeekLow": "52-Week Low",
    "fiftyTwoWeekChange": "52-Week Change", "beta": "Beta",
    "fiftyDayAverage": "50-Day Average",
    "twoHundredDayAverage": "200-Day Average",
}


def _category_for_definition(key: str) -> str:
    if key in _INCOME_STMT_KEYS:
        return "Income Statement"
    if key in _BALANCE_SHEET_KEYS:
        return "Balance Sheet"
    if key in _CASHFLOW_KEYS:
        return "Cash Flow"
    return "Other"


def _build_glossary() -> dict[str, dict]:
    glossary = {}

    # 1. Populate from METRIC_DEFINITIONS (financial statement rows)
    for key, short in METRIC_DEFINITIONS.items():
        glossary[key] = {
            "short": short,
            "explanation": None,
            "example": None,
            "formula": None,
            "components": None,
            "category": _category_for_definition(key),
            "related": None,
        }

    # 2. Populate from METRIC_TOOLTIPS (info analysis metrics)
    for key, short in METRIC_TOOLTIPS.items():
        label = _INFO_LABELS.get(key, key)
        if label not in glossary:
            glossary[label] = {
                "short": short,
                "explanation": None,
                "example": None,
                "formula": None,
                "components": None,
                "category": _INFO_CATEGORIES.get(key, "Other"),
                "related": None,
            }

    # 3. Enrich key metrics with detailed content
    _enrich_glossary(glossary)

    return glossary


def _enrich_glossary(g: dict) -> None:
    """Add detailed explanations, examples, formulas, and related terms for key metrics."""

    # --- Income Statement key metrics ---

    g["Total Revenue"].update({
        "explanation": (
            "Total Revenue represents the full amount of income a company generates "
            "from its business activities before any costs or expenses are subtracted. "
            "It includes revenue from all sources: product sales, service fees, "
            "licensing, subscriptions, and any other operating income. This is the "
            "top line of the income statement and the starting point for evaluating "
            "a company's size and growth trajectory. Consistent revenue growth over "
            "time is one of the most important indicators of a healthy business."
        ),
        "example": (
            "If a company sells 1,000 units at $50 each and also earns $5,000 in "
            "service fees, its total revenue is $55,000. Even if the company loses "
            "money after expenses, the revenue figure shows how much demand exists "
            "for its products and services."
        ),
        "related": ["Operating Revenue", "Gross Profit", "Cost Of Revenue"],
    })

    g["Gross Profit"].update({
        "explanation": (
            "Gross Profit measures how much money remains after subtracting the direct "
            "costs of producing goods or services (Cost of Revenue) from Total Revenue. "
            "It reflects how efficiently a company turns raw materials and labor into "
            "products. A high gross profit suggests strong pricing power or efficient "
            "production. Comparing gross profit margins across companies in the same "
            "industry reveals who has the best cost structure."
        ),
        "example": (
            "A company with $100M in revenue and $60M in cost of goods sold has a "
            "gross profit of $40M, giving it a 40% gross margin. A competitor with "
            "$80M revenue but only $30M in costs has $50M gross profit (62.5% margin), "
            "suggesting better pricing power or cost efficiency."
        ),
        "formula": "Total Revenue - Cost of Revenue",
        "components": ["Total Revenue", "Cost Of Revenue"],
        "related": ["Operating Income", "Net Income"],
    })

    g["Cost Of Revenue"].update({
        "explanation": (
            "Cost of Revenue (also called Cost of Goods Sold or COGS) includes all "
            "direct costs attributable to producing the goods or services that a "
            "company sells. For a manufacturer, this includes raw materials, factory "
            "labor, and manufacturing overhead. For a software company, it might "
            "include hosting costs, licensing fees, and support staff directly tied "
            "to delivering the product."
        ),
        "example": (
            "A bakery generating $500,000 in revenue spends $200,000 on flour, sugar, "
            "butter, bakery staff wages, and oven utilities. That $200,000 is the cost "
            "of revenue. The remaining $300,000 is gross profit, before rent, marketing, "
            "and administrative costs."
        ),
        "related": ["Total Revenue", "Gross Profit"],
    })

    g["Operating Income"].update({
        "explanation": (
            "Operating Income (also called Operating Profit or EBIT in some contexts) "
            "represents the profit a company earns from its core business operations "
            "after deducting all operating expenses including cost of revenue, SG&A, "
            "R&D, and depreciation. It excludes interest and taxes, making it a pure "
            "measure of how well management runs the business. A growing operating "
            "income suggests improving efficiency or successful scaling."
        ),
        "example": (
            "A company with $200M revenue, $120M cost of revenue, and $50M in "
            "operating expenses (salaries, rent, marketing) earns $30M in operating "
            "income. This means the core business generates $0.15 of operating profit "
            "per dollar of revenue (15% operating margin)."
        ),
        "formula": "Gross Profit - Operating Expenses",
        "components": ["Gross Profit", "Operating Expense"],
        "related": ["EBIT", "EBITDA", "Net Income"],
    })

    g["Operating Expense"].update({
        "explanation": (
            "Operating Expenses are the costs required to run the business beyond "
            "direct production costs. They include selling, general and administrative "
            "expenses (SG&A), research and development (R&D), depreciation, and other "
            "day-to-day costs. Managing operating expenses efficiently is critical to "
            "profitability. High operating expenses relative to revenue can indicate "
            "an inefficient business or one that is investing heavily for future growth."
        ),
        "example": (
            "A tech company with $50M revenue spends $15M on R&D, $10M on sales and "
            "marketing, and $5M on administrative costs. Total operating expenses are "
            "$30M, leaving operating income of $20M (after subtracting cost of revenue "
            "from gross profit)."
        ),
        "related": ["Selling General And Administration", "Research And Development", "Operating Income"],
    })

    g["Net Income"].update({
        "explanation": (
            "Net Income is the bottom line — the total profit remaining after all "
            "expenses, interest, taxes, and other deductions. It represents the actual "
            "earnings available to shareholders. Consistent net income growth is a "
            "strong indicator of a well-managed company. Net income is used to "
            "calculate key metrics like earnings per share (EPS) and is the basis "
            "for dividend payments."
        ),
        "example": (
            "A company earns $100M in revenue, spends $60M on costs and expenses, "
            "pays $5M in interest, and $8M in taxes. Net income is $27M. If there are "
            "10M shares outstanding, EPS would be $2.70."
        ),
        "formula": "Pretax Income - Tax Provision",
        "components": ["Pretax Income", "Tax Provision"],
        "related": ["Basic EPS", "Diluted EPS", "Net Income Common Stockholders"],
    })

    g["EBITDA"].update({
        "explanation": (
            "EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) "
            "is a widely used proxy for operating cash flow. By adding back non-cash "
            "charges (depreciation and amortization) and removing the effects of "
            "financing decisions (interest) and tax jurisdictions, EBITDA enables "
            "comparison between companies with different capital structures, tax rates, "
            "and asset bases. It is commonly used in valuation multiples (EV/EBITDA)."
        ),
        "example": (
            "A company has operating income of $50M, depreciation of $10M, and "
            "amortization of $3M. Its EBITDA is $63M. Even though the company reports "
            "$50M in operating profit, it actually generated $63M in cash-like earnings "
            "since D&A are non-cash charges."
        ),
        "formula": "Operating Income + Depreciation & Amortization",
        "components": ["Operating Income", "Depreciation And Amortization"],
        "related": ["EBIT", "Normalized EBITDA", "Operating Cash Flow"],
    })

    g["Basic EPS"].update({
        "explanation": (
            "Basic Earnings Per Share divides net income available to common "
            "shareholders by the weighted average number of common shares outstanding. "
            "It tells you how much profit each share of stock earned. Investors use "
            "EPS trends to gauge profitability growth and to calculate the P/E ratio. "
            "Basic EPS does not account for potential dilution from stock options or "
            "convertible securities."
        ),
        "example": (
            "If a company earns $50M in net income and has 25M shares outstanding, "
            "Basic EPS is $2.00. If the stock trades at $40, the P/E ratio is 20x."
        ),
        "formula": "Net Income Common Stockholders / Basic Average Shares",
        "components": ["Net Income Common Stockholders", "Basic Average Shares"],
        "related": ["Diluted EPS", "Net Income"],
    })

    g["Diluted EPS"].update({
        "explanation": (
            "Diluted EPS accounts for all potential shares that could exist if stock "
            "options, warrants, and convertible securities were exercised. This gives "
            "a more conservative view of per-share earnings. The difference between "
            "basic and diluted EPS reveals how much potential dilution exists. A large "
            "gap may indicate heavy use of stock-based compensation."
        ),
        "example": (
            "A company earns $50M with 25M basic shares and 2M shares from options. "
            "Diluted EPS = $50M / 27M = $1.85, compared to basic EPS of $2.00. The "
            "7.5% dilution comes from employee stock options."
        ),
        "formula": "Net Income Common Stockholders / Diluted Average Shares",
        "components": ["Net Income Common Stockholders", "Diluted Average Shares"],
        "related": ["Basic EPS", "Diluted Average Shares"],
    })

    # --- Balance Sheet key metrics ---

    g["Total Assets"].update({
        "explanation": (
            "Total Assets represent everything a company owns that has economic value. "
            "This includes cash, investments, receivables, inventory, property, "
            "equipment, patents, and goodwill. Total assets must equal total liabilities "
            "plus stockholders' equity (the accounting equation). Growth in total assets "
            "can indicate expansion, while declining assets may signal divestitures or "
            "asset write-downs."
        ),
        "example": (
            "A company has $10B in cash, $5B in receivables, $20B in property and "
            "equipment, and $15B in intangible assets. Total assets are $50B. If total "
            "liabilities are $30B, stockholders' equity is $20B."
        ),
        "formula": "Total Liabilities + Stockholders' Equity",
        "related": ["Current Assets", "Total Non Current Assets", "Stockholders Equity"],
    })

    g["Total Liabilities Net Minority Interest"].update({
        "explanation": (
            "This represents all financial obligations the company owes to external "
            "parties, excluding the minority interest portion. It includes short-term "
            "payables, long-term debt, deferred revenue, pension obligations, and all "
            "other liabilities. Comparing total liabilities to total assets or equity "
            "reveals the company's leverage and financial risk."
        ),
        "example": (
            "A company owes $5B in accounts payable, $15B in long-term debt, and $3B "
            "in other obligations. Total liabilities are $23B. With $50B in assets, "
            "the debt-to-asset ratio is 46%."
        ),
        "related": ["Current Liabilities", "Long Term Debt", "Total Debt", "Stockholders Equity"],
    })

    g["Stockholders Equity"].update({
        "explanation": (
            "Stockholders' Equity (also called shareholders' equity or book value) "
            "represents the net worth of the company — what would remain if all assets "
            "were sold and all debts paid. It consists of capital invested by "
            "shareholders (common stock + additional paid-in capital) plus accumulated "
            "profits kept in the business (retained earnings), minus treasury stock. "
            "Growing equity over time indicates the company is building value."
        ),
        "example": (
            "A company has $50B in total assets and $30B in total liabilities. "
            "Stockholders' equity is $20B. This breaks down into $5B in common stock "
            "and paid-in capital, $18B in retained earnings, and -$3B in treasury stock "
            "from share buybacks."
        ),
        "formula": "Total Assets - Total Liabilities",
        "components": ["Total Assets", "Total Liabilities Net Minority Interest"],
        "related": ["Retained Earnings", "Common Stock Equity", "Tangible Book Value"],
    })

    g["Total Debt"].update({
        "explanation": (
            "Total Debt is the sum of all short-term and long-term borrowings, "
            "including bonds, bank loans, credit lines, and capital lease obligations. "
            "It is a key measure of financial leverage. High debt levels increase "
            "interest expenses and financial risk, especially during economic downturns. "
            "Compare total debt to EBITDA (Debt/EBITDA ratio) to assess how many years "
            "of earnings it would take to repay all debt."
        ),
        "example": (
            "A company has $2B in short-term debt and $8B in long-term bonds. Total "
            "debt is $10B. With EBITDA of $5B, the Debt/EBITDA ratio is 2.0x, meaning "
            "it would take 2 years of EBITDA to repay all debt."
        ),
        "formula": "Current Debt + Long Term Debt",
        "components": ["Current Debt", "Long Term Debt"],
        "related": ["Net Debt", "Long Term Debt", "Current Debt"],
    })

    g["Net Debt"].update({
        "explanation": (
            "Net Debt subtracts cash and short-term investments from total debt. "
            "It reveals the true debt burden after accounting for liquid assets the "
            "company could immediately use to repay debt. A negative net debt means "
            "the company has more cash than debt — a strong financial position. Net "
            "debt is used in Enterprise Value calculations."
        ),
        "example": (
            "A company has $10B total debt and $4B in cash and investments. Net debt "
            "is $6B. A competitor with $8B debt but $9B cash has negative net debt "
            "of -$1B, meaning it could pay off all debt and still have $1B left."
        ),
        "formula": "Total Debt - Cash and Short Term Investments",
        "components": ["Total Debt", "Cash Cash Equivalents And Short Term Investments"],
        "related": ["Total Debt", "Cash And Cash Equivalents"],
    })

    g["Cash And Cash Equivalents"].update({
        "explanation": (
            "Cash and Cash Equivalents include physical currency, bank deposits, and "
            "highly liquid short-term investments (maturing within 90 days) such as "
            "Treasury bills and money market funds. This is the most liquid asset on "
            "the balance sheet. Sufficient cash reserves provide a safety buffer "
            "against unexpected expenses and enable the company to seize opportunities "
            "without needing to borrow."
        ),
        "example": (
            "A company has $3B in bank accounts and $2B in 30-day Treasury bills. "
            "Cash and cash equivalents total $5B. This represents about 3 months of "
            "operating expenses, providing a comfortable liquidity cushion."
        ),
        "related": ["Cash Cash Equivalents And Short Term Investments", "Working Capital"],
    })

    g["Cash Cash Equivalents And Short Term Investments"].update({
        "explanation": (
            "This combines cash, cash equivalents, and short-term investments "
            "(securities maturing within one year). It represents the company's total "
            "liquid reserves — money that can be accessed relatively quickly. This "
            "broader measure is often used when calculating net debt or assessing a "
            "company's ability to weather downturns."
        ),
        "example": (
            "A company holds $5B in cash and equivalents plus $3B in 6-month "
            "corporate bonds. The combined liquid position is $8B."
        ),
        "related": ["Cash And Cash Equivalents", "Other Short Term Investments", "Net Debt"],
    })

    g["Current Assets"].update({
        "explanation": (
            "Current Assets are resources expected to be converted to cash or consumed "
            "within one year. They include cash, accounts receivable, inventory, and "
            "prepaid expenses. Current assets are compared to current liabilities to "
            "assess short-term liquidity (current ratio). A company needs enough "
            "current assets to cover its near-term obligations."
        ),
        "example": (
            "A company has $5B cash, $3B receivables, $2B inventory, and $0.5B "
            "prepaid expenses. Total current assets are $10.5B. With $7B in current "
            "liabilities, the current ratio is 1.5x."
        ),
        "related": ["Current Liabilities", "Working Capital", "Cash And Cash Equivalents"],
    })

    g["Current Liabilities"].update({
        "explanation": (
            "Current Liabilities are obligations the company must settle within one "
            "year, including accounts payable, short-term debt, accrued expenses, and "
            "the current portion of long-term debt. Managing current liabilities "
            "relative to current assets is essential for maintaining liquidity."
        ),
        "example": (
            "A company owes $4B to suppliers, $1.5B in short-term debt, and $1.5B "
            "in accrued wages and taxes. Total current liabilities are $7B."
        ),
        "related": ["Current Assets", "Working Capital", "Accounts Payable"],
    })

    g["Working Capital"].update({
        "explanation": (
            "Working Capital measures the difference between current assets and current "
            "liabilities. Positive working capital means the company can cover its "
            "short-term obligations; negative working capital may indicate liquidity "
            "problems (though some industries like retail routinely operate with "
            "negative working capital due to fast inventory turnover and deferred "
            "customer payments)."
        ),
        "example": (
            "A company has $10B in current assets and $7B in current liabilities. "
            "Working capital is $3B, providing a buffer for unexpected expenses or "
            "temporary revenue dips."
        ),
        "formula": "Current Assets - Current Liabilities",
        "components": ["Current Assets", "Current Liabilities"],
        "related": ["Current Ratio", "Cash And Cash Equivalents"],
    })

    g["Net PPE"].update({
        "explanation": (
            "Net Property, Plant & Equipment is the value of all physical assets "
            "(buildings, machinery, vehicles, land) after subtracting accumulated "
            "depreciation. It represents the current book value of the company's "
            "tangible infrastructure. Capital-intensive businesses like manufacturing "
            "or utilities have high Net PPE relative to revenue."
        ),
        "example": (
            "A factory originally cost $100M (Gross PPE). After 10 years of use, "
            "accumulated depreciation is $40M. Net PPE is $60M, reflecting the "
            "remaining useful value of the asset on the books."
        ),
        "formula": "Gross PPE - Accumulated Depreciation",
        "components": ["Gross PPE", "Accumulated Depreciation"],
        "related": ["Capital Expenditure", "Depreciation And Amortization"],
    })

    g["Goodwill And Other Intangible Assets"].update({
        "explanation": (
            "This combines goodwill (the premium paid in acquisitions above fair value "
            "of net assets) with other intangible assets like patents, trademarks, "
            "and customer relationships. Intangible assets can be significant for "
            "technology and pharmaceutical companies. Unlike physical assets, goodwill "
            "is not amortized but is tested annually for impairment."
        ),
        "example": (
            "A company acquires a competitor for $500M when the target's net assets "
            "are worth $350M. The $150M difference is recorded as goodwill. Combined "
            "with $50M in patents, total intangible assets are $200M."
        ),
        "related": ["Goodwill", "Other Intangible Assets", "Tangible Book Value"],
    })

    g["Retained Earnings"].update({
        "explanation": (
            "Retained Earnings represent the cumulative net income that has been "
            "reinvested in the business rather than paid out as dividends. Growing "
            "retained earnings indicate the company is profitable and choosing to "
            "fund growth internally. Negative retained earnings (accumulated deficit) "
            "mean the company has lost more money over its lifetime than it has earned."
        ),
        "example": (
            "A company has earned $500M in cumulative net income since inception and "
            "paid $150M in total dividends. Retained earnings are $350M. This capital "
            "has been reinvested in R&D, new factories, and acquisitions."
        ),
        "related": ["Net Income", "Cash Dividends Paid", "Stockholders Equity"],
    })

    g["Tangible Book Value"].update({
        "explanation": (
            "Tangible Book Value is stockholders' equity minus intangible assets and "
            "goodwill. It represents the net value of physical, tangible assets the "
            "company owns. This is a conservative measure of a company's worth since "
            "it excludes assets that can be difficult to sell (like goodwill). "
            "Price-to-tangible-book ratios below 1 may indicate undervaluation."
        ),
        "example": (
            "A company has $20B in stockholders' equity, $5B in goodwill, and $2B "
            "in other intangibles. Tangible book value is $13B. With 1B shares "
            "outstanding, tangible book value per share is $13."
        ),
        "formula": "Stockholders' Equity - Goodwill - Other Intangible Assets",
        "components": ["Stockholders Equity", "Goodwill", "Other Intangible Assets"],
        "related": ["Stockholders Equity", "Goodwill And Other Intangible Assets"],
    })

    # --- Cash Flow key metrics ---

    g["Operating Cash Flow"].update({
        "explanation": (
            "Operating Cash Flow is the actual cash generated by the company's core "
            "business operations. Unlike net income (which includes non-cash items "
            "like depreciation), operating cash flow shows real money flowing in. "
            "It starts with net income and adjusts for non-cash charges, then factors "
            "in changes in working capital. Consistently positive operating cash flow "
            "is essential for a sustainable business."
        ),
        "example": (
            "A company reports $50M net income, adds back $15M depreciation, $5M "
            "stock-based compensation, and sees a $3M increase in receivables (cash "
            "outflow). Operating cash flow is $67M. Despite only $50M in accounting "
            "profit, the business actually generated $67M in cash."
        ),
        "related": ["Free Cash Flow", "Net Income", "Change In Working Capital"],
    })

    g["Free Cash Flow"].update({
        "explanation": (
            "Free Cash Flow is the cash remaining after the company pays for capital "
            "expenditures needed to maintain and grow its asset base. It represents "
            "the cash truly available to return to shareholders through dividends and "
            "buybacks, pay down debt, or invest in new opportunities. Consistently "
            "growing free cash flow is one of the strongest indicators of financial "
            "health."
        ),
        "example": (
            "A company generates $80M in operating cash flow and spends $25M on "
            "capital expenditures (new equipment, facility upgrades). Free cash flow "
            "is $55M. Management can use this to pay $20M in dividends, buy back "
            "$15M in stock, and save $20M."
        ),
        "formula": "Operating Cash Flow - Capital Expenditure",
        "components": ["Operating Cash Flow", "Capital Expenditure"],
        "related": ["Operating Cash Flow", "Capital Expenditure", "Cash Dividends Paid"],
    })

    g["Capital Expenditure"].update({
        "explanation": (
            "Capital Expenditure (CapEx) is the cash spent on acquiring or upgrading "
            "physical assets like property, plants, equipment, and technology "
            "infrastructure. CapEx is essential for maintaining competitiveness and "
            "growing capacity. High CapEx relative to revenue is typical of capital-"
            "intensive industries like manufacturing, telecom, and utilities. CapEx "
            "is subtracted from operating cash flow to calculate free cash flow."
        ),
        "example": (
            "A manufacturing company spends $30M on a new production line, $10M "
            "upgrading existing equipment, and $5M on office renovations. Total CapEx "
            "is $45M. This investment should generate additional revenue in future years."
        ),
        "related": ["Free Cash Flow", "Operating Cash Flow", "Net PPE"],
    })

    g["Investing Cash Flow"].update({
        "explanation": (
            "Investing Cash Flow captures all cash spent on or received from long-term "
            "investments. This includes capital expenditures, acquisitions, sales of "
            "business units, and purchases/sales of investment securities. Negative "
            "investing cash flow is normal and usually indicates the company is "
            "investing in its future growth."
        ),
        "example": (
            "A company spends $45M on CapEx, $100M acquiring a competitor, and "
            "receives $20M from selling an investment. Net investing cash flow is "
            "-$125M. Despite being negative, this investment could drive future growth."
        ),
        "related": ["Capital Expenditure", "Net Business Purchase And Sale"],
    })

    g["Financing Cash Flow"].update({
        "explanation": (
            "Financing Cash Flow shows cash flows between the company and its "
            "investors/lenders. This includes proceeds from issuing debt or equity, "
            "repayments of debt, share buybacks, and dividend payments. Negative "
            "financing cash flow often indicates a mature company returning cash to "
            "shareholders, while positive flow suggests the company is raising capital."
        ),
        "example": (
            "A company repays $50M in debt, pays $20M in dividends, and buys back "
            "$30M in shares. Net financing cash flow is -$100M. This shows the company "
            "is returning significant cash to stakeholders."
        ),
        "related": ["Cash Dividends Paid", "Net Common Stock Issuance", "Net Issuance Payments Of Debt"],
    })

    g["Cash Dividends Paid"].update({
        "explanation": (
            "Cash Dividends Paid represents the total cash distributed to shareholders "
            "as dividend payments during the period. This appears as a negative number "
            "in the cash flow statement (cash outflow). Consistent or growing dividends "
            "signal management's confidence in future cash flows."
        ),
        "example": (
            "A company with 100M shares outstanding pays a quarterly dividend of $0.50 "
            "per share. Annual cash dividends paid total $200M."
        ),
        "related": ["Free Cash Flow", "Financing Cash Flow", "Retained Earnings"],
    })

    g["Net Common Stock Issuance"].update({
        "explanation": (
            "This is the net result of issuing new common shares minus repurchasing "
            "existing shares (buybacks). A negative number means the company is buying "
            "back more shares than it is issuing, which reduces share count and can "
            "boost EPS. A positive number means the company is raising equity capital."
        ),
        "example": (
            "A company issues $10M in new shares (from employee stock plans) but "
            "repurchases $60M in shares on the open market. Net common stock issuance "
            "is -$50M, indicating significant share buybacks."
        ),
        "formula": "Common Stock Issuance - Common Stock Payments",
        "components": ["Common Stock Issuance", "Common Stock Payments"],
        "related": ["Common Stock Payments", "Financing Cash Flow"],
    })

    g["Net Issuance Payments Of Debt"].update({
        "explanation": (
            "This shows the net effect of borrowing new debt minus repaying existing "
            "debt. A negative number means the company is paying down debt faster than "
            "it borrows (deleveraging). A positive number means it is increasing its "
            "debt load."
        ),
        "example": (
            "A company issues $200M in new bonds and repays $150M in maturing debt. "
            "Net issuance is $50M, meaning total debt increased by $50M."
        ),
        "related": ["Total Debt", "Long Term Debt", "Financing Cash Flow"],
    })

    g["Depreciation And Amortization"].update({
        "explanation": (
            "Depreciation (for physical assets) and Amortization (for intangible "
            "assets) are non-cash charges that spread the cost of long-lived assets "
            "over their useful life. In the cash flow statement, D&A is added back to "
            "net income because no actual cash leaves the company. High D&A relative "
            "to CapEx may indicate aging assets that will need replacement."
        ),
        "example": (
            "A company bought equipment for $100M with a 10-year useful life. Annual "
            "depreciation is $10M. This reduces reported net income by $10M each year "
            "but does not affect cash flow (the cash was spent when purchasing)."
        ),
        "related": ["Capital Expenditure", "Net PPE", "EBITDA"],
    })

    g["Stock Based Compensation"].update({
        "explanation": (
            "Stock-Based Compensation is a non-cash expense recognized when companies "
            "pay employees with stock options or restricted stock units (RSUs). While "
            "it does not reduce cash, it dilutes existing shareholders by increasing "
            "the total share count over time. It is added back in the operating cash "
            "flow calculation because no cash changes hands."
        ),
        "example": (
            "A tech company grants $500M in RSUs to employees. This appears as a $500M "
            "expense on the income statement (reducing net income) but is added back "
            "in operating cash flow since no cash was paid. However, when employees "
            "vest, new shares are created, diluting existing shareholders."
        ),
        "related": ["Diluted EPS", "Operating Cash Flow"],
    })

    g["Change In Working Capital"].update({
        "explanation": (
            "Change in Working Capital captures how changes in current assets and "
            "current liabilities affect cash flow. When a company sells more on credit "
            "(receivables rise) or builds inventory, cash is consumed. When it delays "
            "paying suppliers (payables rise), cash is preserved. These working capital "
            "dynamics can significantly impact actual cash generation."
        ),
        "example": (
            "A company's receivables increase by $5M (customers owe more), inventory "
            "increases by $3M (built up stock), but payables increase by $4M (delayed "
            "payments to suppliers). Net change in working capital is -$4M, meaning "
            "$4M more cash was consumed than released."
        ),
        "related": ["Working Capital", "Change In Receivables", "Change In Inventory"],
    })

    g["Changes In Cash"].update({
        "explanation": (
            "Changes in Cash is the net increase or decrease in the company's cash "
            "position over the period. It equals the sum of operating, investing, and "
            "financing cash flows, plus any effects of exchange rate changes. A "
            "positive change means the company ended the period with more cash."
        ),
        "example": (
            "A company generates $80M from operations, spends $50M on investments, "
            "and returns $40M through financing activities. The net change in cash is "
            "-$10M, meaning the cash balance decreased by $10M."
        ),
        "formula": "Operating Cash Flow + Investing Cash Flow + Financing Cash Flow",
        "components": ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow"],
        "related": ["Beginning Cash Position", "End Cash Position"],
    })

    # --- Info analysis metrics (scored) ---

    if "Market Cap" in g:
        g["Market Cap"].update({
            "explanation": (
                "Market Capitalization is the total market value of all a company's "
                "outstanding shares of stock. It is calculated by multiplying the current "
                "share price by the total number of shares outstanding. Market cap "
                "classifies companies as mega-cap (>$200B), large-cap ($10B-$200B), "
                "mid-cap ($2B-$10B), small-cap ($300M-$2B), or micro-cap (<$300M). "
                "Larger companies tend to be more stable but may grow slower."
            ),
            "example": (
                "A company has 5 billion shares outstanding trading at $150 each. "
                "Its market cap is $750B, making it a mega-cap company."
            ),
            "formula": "Share Price x Shares Outstanding",
            "related": ["Current Price", "Share Issued"],
        })

    if "Trailing P/E" in g:
        g["Trailing P/E"].update({
            "explanation": (
                "The Trailing Price-to-Earnings ratio divides the current stock price "
                "by the actual earnings per share over the last 12 months. It shows how "
                "much investors are willing to pay for each dollar of proven earnings. "
                "A high P/E may indicate high growth expectations or overvaluation; "
                "a low P/E may signal undervaluation or declining business. Always "
                "compare P/E within the same industry, as norms vary significantly."
            ),
            "example": (
                "A stock trading at $100 with trailing EPS of $5 has a P/E of 20x. "
                "This means investors pay $20 for every $1 of earnings. If the "
                "industry average P/E is 15x, the stock may be relatively expensive."
            ),
            "formula": "Current Price / Trailing 12-Month EPS",
            "related": ["Forward P/E", "PEG Ratio", "Basic EPS"],
        })

    if "Forward P/E" in g:
        g["Forward P/E"].update({
            "explanation": (
                "The Forward P/E ratio uses analysts' estimated future earnings "
                "instead of historical earnings. A forward P/E lower than the trailing "
                "P/E suggests analysts expect earnings to grow. The opposite suggests "
                "expected earnings decline. Forward P/E is speculative since it relies "
                "on analyst estimates, which can be wrong."
            ),
            "example": (
                "A stock at $100 with estimated next-year EPS of $6.25 has a forward "
                "P/E of 16x. Its trailing P/E is 20x (based on $5 actual EPS), "
                "suggesting 25% expected earnings growth."
            ),
            "formula": "Current Price / Estimated Future EPS",
            "related": ["Trailing P/E", "PEG Ratio", "Earnings Growth"],
        })

    if "PEG Ratio" in g:
        g["PEG Ratio"].update({
            "explanation": (
                "The Price/Earnings-to-Growth ratio adjusts the P/E ratio for the "
                "company's expected earnings growth rate. A PEG of 1.0 suggests the "
                "stock is fairly valued relative to its growth. Below 1.0 may indicate "
                "undervaluation (the market isn't fully pricing in the growth), while "
                "above 2.0 may suggest overvaluation. PEG is most useful for comparing "
                "companies with different growth rates."
            ),
            "example": (
                "Company A has P/E of 30x and 30% growth = PEG of 1.0. Company B has "
                "P/E of 20x and 5% growth = PEG of 4.0. Despite a lower P/E, Company B "
                "is more expensive relative to its growth."
            ),
            "formula": "P/E Ratio / Earnings Growth Rate",
            "related": ["Trailing P/E", "Earnings Growth"],
        })

    if "Price to Book" in g:
        g["Price to Book"].update({
            "explanation": (
                "Price-to-Book compares the stock's market price to its book value "
                "(net assets) per share. A P/B below 1.0 means the stock trades below "
                "the theoretical liquidation value of the company's assets — potentially "
                "a bargain if assets are solid, or a warning if the business is in "
                "decline. Asset-heavy industries (banks, utilities) typically have "
                "lower P/B ratios than asset-light ones (tech, services)."
            ),
            "example": (
                "A bank stock at $45 with book value per share of $50 has P/B of 0.9x, "
                "suggesting the market values the bank below its net asset value."
            ),
            "formula": "Share Price / Book Value Per Share",
            "related": ["Stockholders Equity", "Tangible Book Value"],
        })

    if "Return on Equity" in g:
        g["Return on Equity"].update({
            "explanation": (
                "Return on Equity measures how effectively management uses "
                "shareholders' invested capital to generate profit. An ROE of 20% "
                "means the company generates $0.20 in profit for every $1 of equity. "
                "Consistently high ROE (above 15%) is a hallmark of competitive "
                "advantage. However, very high ROE can result from high debt (low "
                "equity), so always check leverage alongside ROE."
            ),
            "example": (
                "A company earns $15B net income with $75B in shareholders' equity. "
                "ROE is 20%. A competitor earns $8B on $100B equity = 8% ROE. The "
                "first company uses shareholders' capital more efficiently."
            ),
            "formula": "Net Income / Shareholders' Equity",
            "components": ["Net Income", "Stockholders Equity"],
            "related": ["Return on Assets", "Profit Margin", "Stockholders Equity"],
        })

    if "Return on Assets" in g:
        g["Return on Assets"].update({
            "explanation": (
                "Return on Assets measures how efficiently a company uses its total "
                "asset base to generate profit. Unlike ROE, ROA is not inflated by "
                "leverage because it considers all assets regardless of how they're "
                "financed. An ROA above 5% is generally good; above 10% is excellent. "
                "Asset-light businesses naturally have higher ROA."
            ),
            "example": (
                "A company earns $5B net income on $100B total assets. ROA is 5%. "
                "A software company earning $3B on $15B assets has ROA of 20%, "
                "reflecting the asset-light nature of software businesses."
            ),
            "formula": "Net Income / Total Assets",
            "components": ["Net Income", "Total Assets"],
            "related": ["Return on Equity", "Total Assets"],
        })

    if "Profit Margin" in g:
        g["Profit Margin"].update({
            "explanation": (
                "Profit Margin (Net Margin) shows what percentage of revenue translates "
                "into bottom-line profit after all expenses, interest, and taxes. Higher "
                "margins indicate better cost control and pricing power. Margins vary "
                "widely by industry: software companies often exceed 20%, while grocery "
                "stores may operate at 2-3%. Tracking margin trends over time is more "
                "important than the absolute level."
            ),
            "example": (
                "A company with $100M revenue and $12M net income has a 12% profit "
                "margin. If revenue grows to $120M while net income reaches $18M, "
                "the margin improves to 15%, indicating improving efficiency."
            ),
            "formula": "Net Income / Total Revenue",
            "components": ["Net Income", "Total Revenue"],
            "related": ["Operating Margin", "Gross Margin", "EBITDA Margin"],
        })

    if "Operating Margin" in g:
        g["Operating Margin"].update({
            "explanation": (
                "Operating Margin shows the percentage of revenue remaining after all "
                "operating costs (production, SG&A, R&D, depreciation). It measures "
                "the core business profitability before interest and taxes. An expanding "
                "operating margin means the company is growing revenue faster than "
                "costs — a sign of operating leverage and scalability."
            ),
            "example": (
                "A company earns $500M revenue with $400M in total operating costs. "
                "Operating income is $100M, giving a 20% operating margin. If costs "
                "only rise to $440M when revenue hits $600M, the margin expands to 26.7%."
            ),
            "formula": "Operating Income / Total Revenue",
            "components": ["Operating Income", "Total Revenue"],
            "related": ["Profit Margin", "Gross Margin", "Operating Income"],
        })

    if "Gross Margin" in g:
        g["Gross Margin"].update({
            "explanation": (
                "Gross Margin is gross profit expressed as a percentage of revenue. "
                "It reveals how much money remains after direct production costs to "
                "cover operating expenses and generate profit. Software companies "
                "typically have 70-90% gross margins (low production costs), while "
                "retailers may have 25-35%. A declining gross margin may indicate "
                "rising input costs or competitive pricing pressure."
            ),
            "example": (
                "A company with $200M revenue and $60M cost of goods sold has a gross "
                "margin of 70%. This means $0.70 of every revenue dollar is available "
                "for R&D, marketing, and profit."
            ),
            "formula": "Gross Profit / Total Revenue",
            "components": ["Gross Profit", "Total Revenue"],
            "related": ["Profit Margin", "Operating Margin", "Gross Profit"],
        })

    if "EBITDA Margin" in g:
        g["EBITDA Margin"].update({
            "explanation": (
                "EBITDA Margin expresses EBITDA as a percentage of revenue. It is a "
                "useful proxy for cash flow margin because it excludes non-cash "
                "depreciation and amortization. Comparing EBITDA margins across "
                "companies in the same industry removes differences in capital "
                "structure, tax rates, and depreciation policies."
            ),
            "example": (
                "A company with $500M revenue and $125M EBITDA has a 25% EBITDA "
                "margin. A competitor with $800M revenue and $160M EBITDA has a "
                "20% EBITDA margin, suggesting less efficient operations."
            ),
            "formula": "EBITDA / Total Revenue",
            "components": ["EBITDA", "Total Revenue"],
            "related": ["Profit Margin", "Operating Margin", "EBITDA"],
        })

    if "Current Ratio" in g:
        g["Current Ratio"].update({
            "explanation": (
                "The Current Ratio measures a company's ability to pay short-term "
                "obligations with its short-term assets. A ratio above 1.0 means "
                "current assets exceed current liabilities. Generally, 1.5-2.0 is "
                "considered healthy. Too high (above 3.0) may indicate inefficient "
                "use of assets. Too low (below 1.0) may signal liquidity risk."
            ),
            "example": (
                "A company has $15B in current assets and $10B in current liabilities. "
                "Current ratio is 1.5x, meaning it has $1.50 in liquid assets for every "
                "$1.00 of near-term obligations."
            ),
            "formula": "Current Assets / Current Liabilities",
            "components": ["Current Assets", "Current Liabilities"],
            "related": ["Quick Ratio", "Working Capital"],
        })

    if "Quick Ratio" in g:
        g["Quick Ratio"].update({
            "explanation": (
                "The Quick Ratio (Acid Test) is a stricter liquidity measure that "
                "excludes inventory from current assets, since inventory may take time "
                "to sell. It answers: can the company cover its obligations without "
                "selling inventory? Above 1.0 is generally comfortable. Companies with "
                "fast-selling inventory (like grocery stores) can operate fine with "
                "lower quick ratios."
            ),
            "example": (
                "A company has $15B current assets, $4B inventory, and $10B current "
                "liabilities. Quick ratio is ($15B - $4B) / $10B = 1.1x."
            ),
            "formula": "(Current Assets - Inventory) / Current Liabilities",
            "components": ["Current Assets", "Inventory", "Current Liabilities"],
            "related": ["Current Ratio", "Working Capital"],
        })

    if "Debt to Equity" in g:
        g["Debt to Equity"].update({
            "explanation": (
                "Debt-to-Equity ratio compares total debt to shareholders' equity. "
                "It reveals how much the company relies on borrowed money versus "
                "shareholder capital. A D/E below 1.0 (or 100%) means the company has "
                "more equity than debt — generally conservative. Higher ratios indicate "
                "more aggressive leverage, which amplifies both returns and risks."
            ),
            "example": (
                "A company with $20B total debt and $40B equity has D/E of 0.5 (50%). "
                "A competitor with $60B debt and $30B equity has D/E of 2.0 (200%), "
                "indicating significantly higher financial risk."
            ),
            "formula": "Total Debt / Stockholders' Equity",
            "components": ["Total Debt", "Stockholders Equity"],
            "related": ["Total Debt", "Stockholders Equity", "Current Ratio"],
        })

    if "Revenue Growth" in g:
        g["Revenue Growth"].update({
            "explanation": (
                "Revenue Growth measures the year-over-year percentage increase in "
                "total revenue. It is the simplest measure of business momentum. "
                "Sustained double-digit growth is a sign of strong market demand and "
                "successful execution. Slowing growth may indicate market saturation "
                "or increased competition."
            ),
            "example": (
                "A company earned $80B last year and $92B this year. Revenue growth "
                "is 15%. If the industry average is 5%, this company is gaining "
                "market share."
            ),
            "formula": "(Current Revenue - Prior Revenue) / Prior Revenue",
            "related": ["Earnings Growth", "Total Revenue"],
        })

    if "Earnings Growth" in g:
        g["Earnings Growth"].update({
            "explanation": (
                "Earnings Growth measures the year-over-year percentage change in "
                "net income or EPS. Growing earnings faster than revenue indicates "
                "margin expansion (improving efficiency). Earnings can grow through "
                "revenue growth, cost cutting, share buybacks, or a combination."
            ),
            "example": (
                "A company's EPS grew from $4.00 to $5.00 year-over-year, representing "
                "25% earnings growth. Revenue only grew 10%, indicating the company "
                "also improved its profit margins."
            ),
            "formula": "(Current Earnings - Prior Earnings) / Prior Earnings",
            "related": ["Revenue Growth", "Net Income", "PEG Ratio"],
        })

    if "Dividend Yield" in g:
        g["Dividend Yield"].update({
            "explanation": (
                "Dividend Yield is the annual dividend payment divided by the current "
                "share price, expressed as a percentage. It shows the cash return from "
                "dividends alone, without considering price appreciation. A high yield "
                "is attractive for income investors, but extremely high yields (above "
                "8%) may signal that the market expects a dividend cut."
            ),
            "example": (
                "A stock at $50 pays $2.00 annually in dividends. Dividend yield is "
                "4.0%. If the stock drops to $40 with the same dividend, yield rises "
                "to 5.0% — but this could signal underlying problems."
            ),
            "formula": "Annual Dividends Per Share / Share Price",
            "related": ["Dividend Rate", "Payout Ratio", "5Y Avg Dividend Yield"],
        })

    if "Payout Ratio" in g:
        g["Payout Ratio"].update({
            "explanation": (
                "The Payout Ratio shows what percentage of net income is paid out as "
                "dividends. A ratio below 60% is generally considered sustainable, "
                "leaving room for reinvestment and a buffer for earnings dips. Above "
                "80% is a warning sign — the company has little margin for error. "
                "Above 100% means the company is paying out more than it earns, which "
                "is unsustainable long-term."
            ),
            "example": (
                "A company earns $4.00 EPS and pays $2.00 in dividends. Payout ratio "
                "is 50%, meaning half of earnings go to shareholders and half is "
                "retained for growth. A 50% payout is considered very sustainable."
            ),
            "formula": "Dividends Per Share / Earnings Per Share",
            "related": ["Dividend Yield", "Net Income", "Free Cash Flow"],
        })

    if "EV / EBITDA" in g:
        g["EV / EBITDA"].update({
            "explanation": (
                "Enterprise Value to EBITDA is a valuation ratio that compares the "
                "total value of a company (including debt, minus cash) to its "
                "operating earnings before non-cash charges. It is preferred over P/E "
                "for comparing companies with different capital structures. Lower "
                "EV/EBITDA generally indicates better value. Typical ranges vary by "
                "industry: tech might be 15-25x, utilities 8-12x."
            ),
            "example": (
                "Company A has $500B enterprise value and $50B EBITDA = 10x EV/EBITDA. "
                "Company B has $200B EV and $25B EBITDA = 8x. Company B appears cheaper "
                "on this metric."
            ),
            "formula": "Enterprise Value / EBITDA",
            "related": ["EBITDA", "Market Cap", "Trailing P/E"],
        })

    if "Beta" in g:
        g["Beta"].update({
            "explanation": (
                "Beta measures a stock's volatility relative to the overall market. "
                "A beta of 1.0 means the stock moves in line with the market. Above "
                "1.0 means more volatile (growth/tech stocks often have beta 1.2-1.5). "
                "Below 1.0 means less volatile (utilities, consumer staples). "
                "Negative beta (very rare) means the stock moves opposite to the market."
            ),
            "example": (
                "A stock with beta 1.3 is expected to move 13% when the market moves "
                "10%. In a bull market this amplifies gains; in a bear market it "
                "amplifies losses."
            ),
            "related": ["52-Week Change", "Current Price"],
        })


# Build the glossary once at module load
GLOSSARY: dict[str, dict] = _build_glossary()
