"""Plain-English tooltip definitions for financial statement metrics."""

METRIC_DEFINITIONS: dict[str, str] = {
    # ── Income Statement ──────────────────────────────────────────────────
    "Total Revenue": (
        "All money earned from selling goods and services before any costs are subtracted."
    ),
    "Operating Revenue": (
        "Revenue from core business operations, excluding non-operating income like investments."
    ),
    "Cost Of Revenue": (
        "Direct costs to produce goods or services sold (materials, labor, manufacturing)."
    ),
    "Gross Profit": (
        "Revenue minus cost of revenue. Shows how much the company earns after production costs."
    ),
    "Operating Expense": (
        "Costs to run the business beyond production: salaries, rent, marketing, R&D."
    ),
    "Selling General And Administration": (
        "Overhead costs: executive salaries, office expenses, marketing, legal fees."
    ),
    "Research And Development": (
        "Money spent on developing new products, technologies, or improving existing ones."
    ),
    "Depreciation And Amortization In Income Statement": (
        "Non-cash charge spreading the cost of assets (equipment, patents) over their useful life."
    ),
    "Depreciation Income Statement": (
        "Portion of depreciation expense for physical assets like buildings and machinery."
    ),
    "Other Operating Expenses": (
        "Miscellaneous operating costs not captured in the main categories above."
    ),
    "Operating Income": (
        "Profit from core operations after all operating expenses. Key measure of business performance."
    ),
    "Total Operating Income As Reported": (
        "Operating income as stated in official filings, before analyst adjustments."
    ),
    "Net Non Operating Interest Income Expense": (
        "Net effect of interest earned minus interest paid, outside core operations."
    ),
    "Interest Income Non Operating": (
        "Interest earned on cash, investments, or loans to others."
    ),
    "Interest Expense Non Operating": (
        "Interest paid on debt (bonds, loans, credit lines). Higher values mean more debt burden."
    ),
    "Total Other Finance Cost": (
        "Non-interest financing costs: loan fees, debt issuance costs, foreign exchange losses."
    ),
    "Net Interest Income": (
        "Interest earned minus interest paid. Positive means the company earns more than it pays."
    ),
    "Interest Income": (
        "Total interest earned from all sources: bank deposits, bonds, loans receivable."
    ),
    "Interest Expense": (
        "Total interest paid on all debt obligations."
    ),
    "Other Income Expense": (
        "Gains or losses outside normal operations: asset sales, lawsuit settlements, one-time items."
    ),
    "Other Non Operating Income Expenses": (
        "Income or expenses from non-core activities like investments, currency gains, or asset sales."
    ),
    "Special Income Charges": (
        "One-time or unusual items: restructuring costs, legal settlements, asset write-downs."
    ),
    "Other Special Charges": (
        "Additional unusual charges not classified elsewhere, typically non-recurring."
    ),
    "Write Off": (
        "Complete removal of an asset's value from the books, recognizing it as worthless."
    ),
    "Impairment Of Capital Assets": (
        "Reduction in recorded value of long-term assets when market value drops below book value."
    ),
    "Restructuring And Mergern Acquisition": (
        "Costs from reorganizing the business or acquiring/merging with other companies."
    ),
    "Pretax Income": (
        "Total profit before income taxes. Shows earning power regardless of tax strategy."
    ),
    "Tax Provision": (
        "Income tax expense for the period. Includes both current taxes owed and deferred taxes."
    ),
    "Net Income Continuous Operations": (
        "Profit from ongoing business activities after taxes, excluding discontinued segments."
    ),
    "Net Income Discontinuous Operations": (
        "Profit or loss from business segments that have been sold or shut down."
    ),
    "Net Income Including Noncontrolling Interests": (
        "Total profit including the share belonging to minority owners of subsidiaries."
    ),
    "Minority Interests": (
        "Portion of subsidiary profits belonging to outside shareholders, not the parent company."
    ),
    "Net Income": (
        "The bottom line: total profit after all expenses, taxes, and minority interests."
    ),
    "Net Income From Continuing And Discontinued Operation": (
        "Combined profit from both ongoing and shut-down business segments."
    ),
    "Net Income From Continuing Operation Net Minority Interest": (
        "Ongoing operations profit minus the share belonging to minority stakeholders."
    ),
    "Net Income Common Stockholders": (
        "Profit available to common shareholders after preferred dividends. Used for EPS calculation."
    ),
    "Diluted NI Availto Com Stockholders": (
        "Net income for common shareholders assuming all convertible securities are exercised."
    ),
    "Otherunder Preferred Stock Dividend": (
        "Preferred stock dividends and other adjustments subtracted before calculating common earnings."
    ),
    "Basic EPS": (
        "Earnings per share using actual shares outstanding. Net income / basic share count."
    ),
    "Diluted EPS": (
        "Earnings per share if all stock options and convertibles were exercised. More conservative than Basic EPS."
    ),
    "Basic Average Shares": (
        "Weighted average number of common shares outstanding during the period."
    ),
    "Diluted Average Shares": (
        "Share count including potential dilution from options, warrants, and convertible securities."
    ),
    "Total Expenses": (
        "Sum of all costs: production, operations, interest, and other expenses."
    ),
    "EBIT": (
        "Earnings Before Interest and Taxes. Measures operating profitability ignoring capital structure."
    ),
    "EBITDA": (
        "Earnings Before Interest, Taxes, Depreciation & Amortization. Proxy for operating cash flow."
    ),
    "Normalized EBITDA": (
        "EBITDA adjusted to remove one-time items, giving a clearer view of recurring profitability."
    ),
    "Normalized Income": (
        "Net income adjusted for unusual or non-recurring items to show sustainable earnings."
    ),
    "Reconciled Cost Of Revenue": (
        "Cost of revenue adjusted for consistency across reporting periods."
    ),
    "Reconciled Depreciation": (
        "Depreciation figure adjusted for comparability, used in normalized calculations."
    ),
    "Total Unusual Items": (
        "Sum of all one-time gains and charges that distort normal earnings comparison."
    ),
    "Total Unusual Items Excluding Goodwill": (
        "One-time items excluding goodwill impairment, which is tracked separately."
    ),
    "Tax Effect Of Unusual Items": (
        "Tax impact of unusual items. Used to calculate after-tax effect of one-time charges."
    ),
    "Tax Rate For Calcs": (
        "Effective tax rate used for normalizing earnings. Actual taxes paid / pretax income."
    ),

    # ── Balance Sheet ─────────────────────────────────────────────────────
    "Total Assets": (
        "Everything the company owns: cash, investments, property, equipment, patents, and receivables."
    ),
    "Current Assets": (
        "Assets expected to be converted to cash within one year: cash, receivables, inventory."
    ),
    "Cash And Cash Equivalents": (
        "Money in the bank plus short-term investments easily converted to cash (T-bills, money market)."
    ),
    "Cash Cash Equivalents And Short Term Investments": (
        "Cash on hand plus short-term securities. The company's liquid reserves."
    ),
    "Cash Equivalents": (
        "Short-term, highly liquid investments that are practically as good as cash."
    ),
    "Cash Financial": (
        "Total cash position including restricted and unrestricted cash holdings."
    ),
    "Other Short Term Investments": (
        "Short-term securities like commercial paper, certificates of deposit, or Treasury bills."
    ),
    "Accounts Receivable": (
        "Money owed by customers for goods or services already delivered. Collected within 30-90 days typically."
    ),
    "Receivables": (
        "All amounts owed to the company: customer invoices, notes, and other receivables."
    ),
    "Other Receivables": (
        "Receivables outside normal trade: tax refunds, insurance claims, employee advances."
    ),
    "Gross Accounts Receivable": (
        "Total receivables before subtracting allowance for doubtful accounts."
    ),
    "Allowance For Doubtful Accounts Receivable": (
        "Estimated amount of receivables unlikely to be collected. Subtracted from gross receivables."
    ),
    "Inventory": (
        "Goods available for sale or raw materials/work-in-progress. Key for manufacturing and retail."
    ),
    "Raw Materials": (
        "Materials purchased for manufacturing that have not yet been processed."
    ),
    "Work In Process": (
        "Partially completed goods still in the manufacturing process."
    ),
    "Finished Goods": (
        "Completed products ready for sale to customers."
    ),
    "Other Inventories": (
        "Inventory items not classified as raw materials, work in process, or finished goods."
    ),
    "Prepaid Assets": (
        "Expenses paid in advance: insurance premiums, rent, subscriptions not yet used."
    ),
    "Other Current Assets": (
        "Miscellaneous short-term assets not classified elsewhere."
    ),
    "Hedging Assets Current": (
        "Fair value of derivative contracts used to hedge risks, maturing within one year."
    ),
    "Assets Held For Sale Current": (
        "Assets the company plans to sell within the next year, carried at fair value."
    ),
    "Total Non Current Assets": (
        "Long-term assets not expected to be converted to cash within one year."
    ),
    "Net PPE": (
        "Net Property, Plant & Equipment: physical assets (buildings, machinery) minus accumulated depreciation."
    ),
    "Gross PPE": (
        "Total original cost of all physical assets before subtracting depreciation."
    ),
    "Land And Improvements": (
        "Cost of land and permanent improvements like grading, paving, and landscaping."
    ),
    "Buildings And Improvements": (
        "Cost of buildings, renovations, and structural improvements."
    ),
    "Machinery Furniture Equipment": (
        "Cost of machinery, office furniture, computers, and other business equipment."
    ),
    "Construction In Progress": (
        "Cost of assets currently being built or installed, not yet placed in service."
    ),
    "Leases": (
        "Capitalized value of long-term leases for property, equipment, or vehicles."
    ),
    "Other Properties": (
        "Physical assets not classified in the main PPE categories."
    ),
    "Properties": (
        "Total value of all physical properties owned by the company."
    ),
    "Accumulated Depreciation": (
        "Total depreciation charged against assets over their life. Subtracted from Gross PPE to get Net PPE."
    ),
    "Goodwill": (
        "Premium paid above fair value when acquiring another company. Reflects brand, reputation, synergies."
    ),
    "Goodwill And Other Intangible Assets": (
        "Goodwill plus patents, trademarks, copyrights, and other non-physical assets."
    ),
    "Other Intangible Assets": (
        "Non-physical assets excluding goodwill: patents, trademarks, customer lists, software."
    ),
    "Investments And Advances": (
        "Long-term investments in other companies, joint ventures, or loans to subsidiaries."
    ),
    "Long Term Equity Investment": (
        "Ownership stakes in other companies held for more than one year."
    ),
    "Investmentin Financial Assets": (
        "Securities and financial instruments held as long-term investments."
    ),
    "Available For Sale Securities": (
        "Investments in debt or equity securities that can be sold but aren't actively traded."
    ),
    "Held To Maturity Securities": (
        "Debt securities the company intends to hold until they mature."
    ),
    "Trading Securities": (
        "Securities bought and sold frequently for short-term profit."
    ),
    "Investment Properties": (
        "Real estate held to earn rental income or for capital appreciation, not business operations."
    ),
    "Non Current Accounts Receivable": (
        "Amounts owed to the company that won't be collected for more than one year."
    ),
    "Non Current Note Receivables": (
        "Formal loan agreements where repayment extends beyond one year."
    ),
    "Non Current Deferred Assets": (
        "Long-term prepaid expenses or deferred charges to be recognized over multiple years."
    ),
    "Non Current Deferred Taxes Assets": (
        "Future tax benefits from temporary differences or tax loss carryforwards."
    ),
    "Defined Pension Benefit": (
        "Net pension asset when the pension fund is overfunded relative to obligations."
    ),
    "Other Non Current Assets": (
        "Long-term assets not fitting other categories: deposits, restricted cash, deferred charges."
    ),
    "Total Liabilities Net Minority Interest": (
        "All company obligations (debt, payables, deferred revenue) excluding minority interest."
    ),
    "Current Liabilities": (
        "Obligations due within one year: accounts payable, short-term debt, accrued expenses."
    ),
    "Accounts Payable": (
        "Money owed to suppliers for goods and services received but not yet paid."
    ),
    "Payables": (
        "All short-term amounts owed: supplier invoices, accrued wages, taxes due."
    ),
    "Payables And Accrued Expenses": (
        "Combined total of accounts payable and expenses incurred but not yet billed."
    ),
    "Total Tax Payable": (
        "Income and other taxes currently owed to government authorities."
    ),
    "Income Tax Payable": (
        "Federal, state, and foreign income taxes owed for the current period."
    ),
    "Current Debt": (
        "Portion of long-term debt due within one year plus any short-term borrowings."
    ),
    "Current Debt And Capital Lease Obligation": (
        "Short-term debt plus current portion of lease obligations."
    ),
    "Current Capital Lease Obligation": (
        "Lease payments due within the next year under capital/finance leases."
    ),
    "Current Deferred Liabilities": (
        "Deferred revenue and other obligations expected to be settled within one year."
    ),
    "Current Deferred Revenue": (
        "Payments received for products or services not yet delivered. Recognized as revenue when fulfilled."
    ),
    "Current Accrued Expenses": (
        "Expenses incurred but not yet paid: salaries, utilities, interest due."
    ),
    "Dividends Payable": (
        "Dividends declared by the board but not yet paid to shareholders."
    ),
    "Pension And Other Post Retirement Benefit Plans Current": (
        "Pension and retiree benefit obligations due within one year."
    ),
    "Other Current Liabilities": (
        "Miscellaneous short-term obligations not classified elsewhere."
    ),
    "Total Non Current Liabilities Net Minority Interest": (
        "Long-term obligations due beyond one year, excluding minority interest."
    ),
    "Long Term Debt": (
        "Bonds, term loans, and other borrowings due in more than one year."
    ),
    "Long Term Debt And Capital Lease Obligation": (
        "Long-term borrowings plus long-term lease obligations combined."
    ),
    "Long Term Capital Lease Obligation": (
        "Lease obligations extending beyond one year under capital/finance leases."
    ),
    "Long Term Provisions": (
        "Estimated long-term liabilities for warranties, environmental cleanup, or legal claims."
    ),
    "Non Current Deferred Liabilities": (
        "Long-term deferred revenue and other obligations to be settled beyond one year."
    ),
    "Non Current Deferred Revenue": (
        "Prepayments for goods or services to be delivered beyond one year."
    ),
    "Non Current Deferred Taxes Liabilities": (
        "Taxes that will be owed in future periods due to temporary timing differences."
    ),
    "Non Current Pension And Other Postretirement Benefit Plans": (
        "Long-term pension and retiree healthcare obligations the company must fund."
    ),
    "Tradeand Other Payables Non Current": (
        "Long-term amounts owed to suppliers or other parties beyond one year."
    ),
    "Other Non Current Liabilities": (
        "Long-term obligations not classified elsewhere: deferred rent, asset retirement obligations."
    ),
    "Total Debt": (
        "Sum of all short-term and long-term borrowings. Key measure of financial leverage."
    ),
    "Net Debt": (
        "Total debt minus cash and short-term investments. Shows true debt burden after liquid assets."
    ),
    "Stockholders Equity": (
        "Company's net worth: total assets minus total liabilities. What shareholders actually own."
    ),
    "Common Stock Equity": (
        "Equity attributable to common shareholders: share capital + retained earnings + other equity."
    ),
    "Capital Stock": (
        "Par value of all issued shares (common and preferred)."
    ),
    "Common Stock": (
        "Par value of issued common shares. Usually a small, nominal amount per share."
    ),
    "Preferred Stock": (
        "Par value of issued preferred shares, which have priority over common stock for dividends."
    ),
    "Additional Paid In Capital": (
        "Amount investors paid above par value when buying shares. Reflects market demand for the stock."
    ),
    "Retained Earnings": (
        "Cumulative profits kept in the business rather than paid as dividends. Funds growth and investment."
    ),
    "Treasury Shares Number": (
        "Number of shares the company has repurchased and holds in treasury."
    ),
    "Treasury Stock": (
        "Cost of shares the company has bought back. Shown as negative equity."
    ),
    "Gains Losses Not Affecting Retained Earnings": (
        "Unrealized gains/losses on investments, pensions, and foreign currency not yet in net income."
    ),
    "Other Equity Adjustments": (
        "Equity changes from foreign currency translation, hedging, and pension adjustments."
    ),
    "Minority Interest": (
        "Equity in subsidiaries owned by outside shareholders, not the parent company."
    ),
    "Total Equity Gross Minority Interest": (
        "Total equity including both parent company shareholders and minority interest holders."
    ),
    "Total Capitalization": (
        "Long-term debt plus stockholders' equity. Represents the company's permanent capital base."
    ),
    "Share Issued": (
        "Total number of shares that have been issued to investors."
    ),
    "Ordinary Shares Number": (
        "Number of common/ordinary shares currently outstanding."
    ),
    "Tangible Book Value": (
        "Stockholders' equity minus intangible assets and goodwill. What's left if you strip out intangibles."
    ),
    "Working Capital": (
        "Current assets minus current liabilities. Measures short-term financial health and liquidity."
    ),
    "Invested Capital": (
        "Total debt plus equity minus cash. Capital actually deployed in the business."
    ),
    "Net Tangible Assets": (
        "Total assets minus intangible assets, goodwill, and total liabilities."
    ),

    # ── Cash Flow Statement ───────────────────────────────────────────────
    "Operating Cash Flow": (
        "Cash generated from core business operations. The most important cash flow measure."
    ),
    "Cash Flow From Continuing Operating Activities": (
        "Operating cash flow from ongoing business segments, excluding discontinued operations."
    ),
    "Net Income From Continuing Operations": (
        "Net income from ongoing operations, starting point for operating cash flow calculation."
    ),
    "Depreciation And Amortization": (
        "Non-cash charge added back to net income. Spreads asset costs over their useful life."
    ),
    "Depreciation Amortization Depletion": (
        "Combined non-cash charges for physical asset wear, intangible asset usage, and natural resource extraction."
    ),
    "Deferred Tax": (
        "Tax expense recognized now but not yet paid (or tax paid now but not yet expensed)."
    ),
    "Deferred Income Tax": (
        "Change in deferred tax assets/liabilities. Non-cash adjustment to operating cash flow."
    ),
    "Stock Based Compensation": (
        "Non-cash expense for employee stock options and restricted stock grants. Added back in cash flow."
    ),
    "Other Non Cash Items": (
        "Miscellaneous non-cash charges or credits adjusted in operating cash flow."
    ),
    "Change In Working Capital": (
        "Net change in current assets and liabilities. Negative means the business is consuming more cash."
    ),
    "Change In Receivables": (
        "Increase in receivables uses cash (more money owed); decrease frees cash."
    ),
    "Changes In Account Receivables": (
        "Change in customer receivables. Rising receivables can signal collection issues."
    ),
    "Change In Inventory": (
        "Increase in inventory uses cash (buying stock); decrease frees cash (selling down)."
    ),
    "Change In Payables And Accrued Expense": (
        "Increase in payables provides cash (delaying payments); decrease uses cash."
    ),
    "Change In Payable": (
        "Change in amounts owed to suppliers. Rising payables temporarily boost cash."
    ),
    "Change In Account Payable": (
        "Change in trade payables specifically for supplier invoices."
    ),
    "Change In Accrued Expense": (
        "Change in accrued but unpaid expenses like wages, interest, and utilities."
    ),
    "Change In Tax Payable": (
        "Change in taxes owed. Increase means more tax accrued but not yet paid."
    ),
    "Change In Income Tax": (
        "Change in income tax payable or receivable positions."
    ),
    "Change In Prepaid Assets": (
        "Change in prepaid expenses. Paying ahead uses cash; using up prepaid items frees cash."
    ),
    "Change In Other Working Capital": (
        "Changes in miscellaneous working capital items not categorized elsewhere."
    ),
    "Change In Other Current Assets": (
        "Changes in miscellaneous current assets affecting operating cash flow."
    ),
    "Change In Other Current Liabilities": (
        "Changes in miscellaneous current liabilities affecting operating cash flow."
    ),
    "Provisionand Write Offof Assets": (
        "Non-cash charges for asset impairments and write-offs added back in cash flow."
    ),
    "Asset Impairment Charge": (
        "Non-cash charge when an asset's market value drops below its book value."
    ),
    "Gain Loss On Sale Of Business": (
        "Gain or loss from selling a business unit. Removed from operating cash flow as non-recurring."
    ),
    "Gain Loss On Investment Securities": (
        "Realized gains or losses from selling investment securities."
    ),
    "Net Foreign Currency Exchange Gain Loss": (
        "Non-cash gains or losses from translating foreign currency transactions."
    ),
    "Earnings Losses From Equity Investments": (
        "Share of profits or losses from companies where ownership is 20-50% (equity method)."
    ),
    "Pension And Employee Benefit Expense": (
        "Non-cash pension and benefits expense adjusted in operating cash flow."
    ),
    "Operating Gains Losses": (
        "Non-cash operating gains or losses removed to reconcile net income to cash flow."
    ),
    "Investing Cash Flow": (
        "Cash spent on or received from long-term investments: equipment, acquisitions, securities."
    ),
    "Cash Flow From Continuing Investing Activities": (
        "Investing cash flows from ongoing operations, excluding discontinued segments."
    ),
    "Capital Expenditure": (
        "Cash spent on property, plant, and equipment. Essential for maintaining and growing operations."
    ),
    "Net Business Purchase And Sale": (
        "Net cash spent on acquiring businesses minus proceeds from selling business units."
    ),
    "Purchase Of Business": (
        "Cash paid to acquire other companies or business units."
    ),
    "Sale Of Business": (
        "Cash received from selling subsidiaries or business divisions."
    ),
    "Purchase Of Investment": (
        "Cash spent buying investment securities, stakes in other companies, or financial assets."
    ),
    "Sale Of Investment": (
        "Cash received from selling investment securities or stakes in other companies."
    ),
    "Net Investment Purchase And Sale": (
        "Net cash flow from buying and selling investment securities."
    ),
    "Net PPE Purchase And Sale": (
        "Net cash spent on buying minus selling property, plant, and equipment."
    ),
    "Purchase Of PPE": (
        "Cash paid for new property, plant, and equipment (same as capital expenditure)."
    ),
    "Sale Of PPE": (
        "Cash received from selling property, plant, and equipment no longer needed."
    ),
    "Net Intangibles Purchase And Sale": (
        "Net cash flow from buying and selling intangible assets like patents or software."
    ),
    "Purchase Of Intangibles": (
        "Cash spent acquiring intangible assets: patents, licenses, software."
    ),
    "Sale Of Intangibles": (
        "Cash received from selling intangible assets."
    ),
    "Net Other Investing Changes": (
        "Other investing cash flows not classified in main categories."
    ),
    "Financing Cash Flow": (
        "Cash from or returned to investors and lenders: debt, equity, and dividends."
    ),
    "Cash Flow From Continuing Financing Activities": (
        "Financing cash flows from ongoing operations, excluding discontinued segments."
    ),
    "Net Issuance Payments Of Debt": (
        "Net cash from issuing new debt minus repaying existing debt."
    ),
    "Net Long Term Debt Issuance": (
        "Cash from issuing long-term debt minus repayments of long-term debt."
    ),
    "Long Term Debt Issuance": (
        "Cash received from issuing bonds, term loans, or other long-term borrowings."
    ),
    "Long Term Debt Payments": (
        "Cash paid to repay long-term debt obligations (principal payments)."
    ),
    "Net Short Term Debt Issuance": (
        "Net change in short-term borrowings: commercial paper, credit lines, short-term loans."
    ),
    "Short Term Debt Issuance": (
        "Cash received from new short-term borrowings."
    ),
    "Short Term Debt Payments": (
        "Cash paid to repay short-term debt."
    ),
    "Net Common Stock Issuance": (
        "Cash from issuing new common shares minus cash spent on buybacks."
    ),
    "Common Stock Issuance": (
        "Cash received from selling new common shares to investors."
    ),
    "Common Stock Payments": (
        "Cash spent repurchasing the company's own common shares (buybacks)."
    ),
    "Net Preferred Stock Issuance": (
        "Cash from issuing preferred stock minus any preferred stock repurchases."
    ),
    "Preferred Stock Issuance": (
        "Cash received from selling new preferred shares."
    ),
    "Preferred Stock Payments": (
        "Cash spent repurchasing preferred shares."
    ),
    "Proceeds From Stock Option Exercised": (
        "Cash received when employees exercise stock options and buy shares."
    ),
    "Cash Dividends Paid": (
        "Total cash paid out as dividends to all shareholders during the period."
    ),
    "Common Stock Dividend Paid": (
        "Cash dividends paid to common shareholders."
    ),
    "Preferred Stock Dividend Paid": (
        "Cash dividends paid to preferred shareholders."
    ),
    "Net Other Financing Charges": (
        "Other financing cash flows: debt issuance costs, contingent consideration payments."
    ),
    "Issuance Of Capital Stock": (
        "Cash received from issuing any type of stock (common or preferred)."
    ),
    "Repurchase Of Capital Stock": (
        "Cash spent on buying back any type of the company's stock."
    ),
    "Issuance Of Debt": (
        "Total cash received from all new debt issuances (short-term and long-term)."
    ),
    "Repayment Of Debt": (
        "Total cash paid to repay all types of debt."
    ),
    "Free Cash Flow": (
        "Operating cash flow minus capital expenditures. Cash available for dividends, buybacks, or debt paydown."
    ),
    "Changes In Cash": (
        "Net change in cash position: operating + investing + financing cash flows combined."
    ),
    "Effect Of Exchange Rate Changes": (
        "Impact of currency exchange rate changes on cash held in foreign currencies."
    ),
    "Beginning Cash Position": (
        "Cash balance at the start of the period."
    ),
    "End Cash Position": (
        "Cash balance at the end of the period."
    ),
    "Capital Expenditure Reported": (
        "Capital expenditure as reported in the company's official filings."
    ),
}

# Key metrics highlighted in the table, by statement type
KEY_METRICS: dict[str, set[str]] = {
    "income_stmt": {
        "Total Revenue",
        "Gross Profit",
        "Operating Income",
        "Net Income",
        "EBITDA",
        "Basic EPS",
        "Diluted EPS",
        "Operating Expense",
        "Cost Of Revenue",
    },
    "balance_sheet": {
        "Total Assets",
        "Total Liabilities Net Minority Interest",
        "Stockholders Equity",
        "Total Debt",
        "Net Debt",
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
        "Current Assets",
        "Current Liabilities",
        "Working Capital",
        "Net PPE",
        "Goodwill And Other Intangible Assets",
        "Retained Earnings",
        "Tangible Book Value",
    },
    "cashflow": {
        "Operating Cash Flow",
        "Free Cash Flow",
        "Capital Expenditure",
        "Investing Cash Flow",
        "Financing Cash Flow",
        "Cash Dividends Paid",
        "Net Common Stock Issuance",
        "Net Issuance Payments Of Debt",
        "Depreciation And Amortization",
        "Stock Based Compensation",
        "Change In Working Capital",
        "Changes In Cash",
    },
}
