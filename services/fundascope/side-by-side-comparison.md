Side-by-Side Stock Comparison (Stock Info)                              

 Context

 Users analyzing stocks often want to compare two companies' fundamentals side by side. Currently, only one stock can be viewed at a time, requiring manual switching. This feature adds a "Compare" button (visible only for Stock Info)
 that lets the user pick a second ticker and see both stocks' metrics in merged 3-column tables (Metric | Stock A | Stock B). Custom view filtering applies to both sides.

 Design

 Entry Point

 A "Compare" button appears in the header bar (next to Refresh), visible only when statement type is "Stock Info" and data has been loaded. Clicking it opens a small popover with a ticker input (with autocomplete) and a "Go" button.

 [Statement Lens]  [ticker] [stmt type] [Analyze] [Refresh] [Compare]
 [View: Full View ▾]  [+ Create View]  [Delete]  [Exit Comparison]
 ─────────────────────────────────────────────────────
 [Profile A]                    [Profile B]
 [Summary A]                    [Summary B]
 [Scorecard A]                  [Scorecard B]
 ┌─────────────┬──────┬──────┐
 │ Metric      │ AAPL │ MSFT │
 ├─────────────┼──────┼──────┤
 │ Market Cap  │ 3.4T │ 3.1T │
 └─────────────┴──────┴──────┘

 Compare Popover

 A small floating panel anchored below the Compare button:
 - Ticker input with full autocomplete (same behavior as main input)
 - "Go" button to trigger comparison

 Comparison Layout

 - Profile bars, business summaries, scorecards: displayed in a 2-column CSS grid (compare-wrapper)
 - Section tables: merged into 3-column tables (Metric | Stock A | Stock B), one table per section
 - Sections are matched by title; rows are unioned across both stocks; missing values show "---"
 - Section grade badges shown in column headers per stock
 - Tooltips taken from whichever side has them (identical for same metric)

 Custom Views Integration

 The existing getActiveFilterFields() works unchanged. In comparison mode, the filter is applied to both stocks' section rows. Sections that become empty after filtering are hidden. onViewChange() gets a compareMode branch that
 re-renders the comparison.

 State

 Three new variables:
 - compareMode (boolean) — whether comparison is active
 - lastFetchedDataB (object) — second stock's API response
 - tickerB (string) — second stock's ticker symbol

 Exiting Comparison

 An "Exit Comparison" button appears in the view bar during comparison mode. Clicking it resets to single-stock view using lastFetchedData.

 Implementation Steps

 File: templates/index.html — all changes in this single file.

 1. Refactor autocomplete into reusable factory

 Extract the existing hideSuggestions, showSuggestions, doLookup functions and the tickerInput event listeners into a single attachAutocomplete(inputEl, suggestionsEl, onSelect) factory function. This encapsulates per-input state (timer,
  abort controller, selected index) and returns a { hide } handle. Wire the primary ticker input through it, then reuse for the compare ticker input.

 Remove the old standalone functions (hideSuggestions, showSuggestions, doLookup) and the three tickerInput.addEventListener blocks (input, keydown, blur). Replace with two attachAutocomplete() calls.

 2. Add HTML

 - Compare button: after #refreshBtn in the header, add <button class="btn btn-sm" id="compareBtn" style="display:none">Compare</button>
 - Exit Comparison button: inside #viewBar, after #deleteViewBtn, add <button class="btn btn-sm" id="exitCompareBtn" style="display:none">Exit Comparison</button>
 - Compare popover: new markup before <script> — backdrop div + popover div with ticker input, suggestions div, and Go button

 3. Add CSS

 - .compare-backdrop / .compare-popover: floating panel styles (similar to existing modal pattern)
 - .compare-wrapper: display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem
 - .compare-panel: min-width: 0 to prevent grid blowout
 - .compare-table th.col-a: accent color; .compare-table th.col-b: yellow/orange color
 - .compare-active: wider container (max-width: 1800px override)

 4. Add JavaScript

 New state variables (after existing currentStmtType):
 - let compareMode = false;
 - let lastFetchedDataB = null;
 - let tickerB = '';

 New element references:
 - compareBtn, exitCompareBtn, comparePopover, compareBackdrop, compareTickerInput

 New functions:
 - openComparePopover() — position popover below button, show it, focus input
 - closeComparePopover() — hide popover and backdrop
 - startCompare() — fetch both stocks in parallel via Promise.all, set compareMode = true, call renderComparison()
 - renderComparison(dataA, dataB, tickerA, tickerB, filterFields) — builds the full comparison HTML
 - renderProfileBar(profile, ticker) — extracted helper (returns HTML string)
 - renderBizSummary(text) — extracted helper (returns HTML string)
 - renderScorecardSingle(scorecard) — extracted helper from existing renderStockInfo scorecard block
 - exitCompare() — reset state, re-render single stock

 5. Modify existing functions

 - analyze(): after successful stock-info fetch, show/hide compareBtn based on isStockInfo. If compareMode was active and user re-analyzes, exit comparison.
 - onViewChange(): add compareMode branch that calls renderComparison() with current filter
 - renderStockInfo(): refactor to use the new renderProfileBar, renderBizSummary, renderScorecardSingle helpers (keeps behavior identical, just DRY)
 - stmtType change listener: hide compareBtn when not stock_info; exit comparison if active

 Files Modified

 - templates/index.html — all changes in this single file (HTML + CSS + JS)

 Verification

 1. Start the server: python app.py
 2. Search for AAPL, select "Stock Info" → Analyze → confirm "Compare" button appears
 3. Click "Compare" → type MSFT in popover → verify autocomplete works → click Go
 4. Verify comparison layout: two profile bars, two scorecards, merged 3-column section tables
 5. Verify metrics align by label; missing metrics on one side show "---"
 6. Select a custom view → verify both columns filter to the same fields
 7. Switch back to "Full View" → verify all metrics reappear
 8. Click "Exit Comparison" → verify single-stock view returns
 9. Switch statement type to "Income Statement" → verify Compare button disappears
 10. Switch back to "Stock Info" → Analyze → verify Compare button reappears
