Custom Views Feature                                                    

 Context

 The app displays dense financial data across 7 statement types (stock_info, income_stmt, etc.). Users need a way to focus on specific fields rather than scrolling through all metrics. Custom views let users save named subsets of fields
 per statement type and quickly switch between them via a dropdown.

 Design

 UI: Dropdown bar below the header

 A new bar appears between the header and the content area, containing:
 - A <select> dropdown (id viewSelect) with options: "Full View" (default), plus any saved custom views for the current statement type
 - A "Create View" button that opens a modal for building a new view
 - A "Delete" button (visible only when a custom view is selected)

 [Statement Lens]  [ticker] [stmt type] [Analyze] [Refresh]
 [View: Full View ▾]  [+ Create View]  [🗑 Delete
 ─────────────────────────────────────────────────────
 [content...]

 Modal: Create/Edit View

 A modal dialog (similar in style to the existing chat modal) with:
 - A text input for the view name
 - A checklist of all available fields for the current statement type, grouped by section
   - For stock_info: fields grouped under Valuation, Profitability, Financial Health, Growth, Dividends, Price & Trading
   - For financial statements: all row labels from the table (e.g., Total Revenue, Cost Of Revenue, etc.)
 - "Select All" / "Deselect All" buttons
 - A "Save" button

 Storage: localStorage

 Custom views stored in localStorage under key statementLens_customViews:
 {
   "stock_info": [
     { "name": "Quick Valuation", "fields": ["Market Cap", "Trailing P/E", "PEG Ratio"] }
   ],
   "income_stmt": [
     { "name": "Revenue Focus", "fields": ["Total Revenue", "Cost Of Revenue", "Gross Profit"] }
   ]
 }

 Filtering Logic

 When a custom view is selected:
 - Stock Info (renderStockInfo): filter section.rows to only include rows whose label is in the view's fields list. Hide sections that end up empty. Scorecard and profile bar always shown.
 - Financial Statements (renderTable): filter rows to only include those whose label is in the view's fields list. Scorecard, margins bar, and dividend safety panel always shown.
 - When "Full View" is selected, no filtering — show everything as today.

 Field Discovery

 The available fields are extracted from the last fetched data:
 - Stock info: iterate data.sections[].rows[].label
 - Statements: iterate data.rows[].label

 This means the "Create View" button is only enabled after data has been loaded. The field list in the modal is dynamically built from the actual API response.

 Implementation Steps

 1. Add HTML for the view bar and modal

 File: templates/index.html

 Below the .header div (after line ~653), add:
 - A div.view-bar containing the select, create button, and delete button
 - A div.view-modal + backdrop for the create view dialog (name input, field checklist, save button)

 2. Add CSS styles

 File: templates/index.html (style section)

 - .view-bar: flex row, gap, align-items center, margin-bottom, matching existing theme
 - .view-modal: fixed position modal (like chat modal), with checklist styling
 - .field-checklist: scrollable area with checkboxes
 - .view-section-group: section headers within the checklist

 3. Add JavaScript logic

 File: templates/index.html (script section)

 State variables:
 - let lastFetchedData = null; — store the most recent API response
 - let currentStmtType = ''; — track which statement type was last loaded

 Functions:
 - loadCustomViews() — read from localStorage, return parsed object
 - saveCustomViews(views) — write to localStorage
 - populateViewDropdown() — fill the select with views for currentStmtType
 - onViewChange() — re-render data with filtering applied
 - openCreateViewModal() — populate field checklist from lastFetchedData, show modal
 - saveNewView() — read name + checked fields, save to localStorage, refresh dropdown
 - deleteCurrentView() — remove selected view, switch back to Full View

 Modifications to existing functions:
 - analyze(): after fetching data, store it in lastFetchedData, set currentStmtType, call populateViewDropdown()
 - renderStockInfo(data) and renderAnalysis(data): accept an optional filterFields array parameter. When set, filter rows/section.rows to only those whose label is in the array.

 4. Wire up event handlers

 - viewSelect.onchange → onViewChange()
 - Create View button → openCreateViewModal()
 - Delete button → deleteCurrentView() with confirmation
 - Save button in modal → saveNewView()

 Files Modified

 - templates/index.html — all changes in this single file (HTML + CSS + JS)

 Verification

 1. Start the server: python app.py
 2. Search for a ticker (e.g., AAPL) and select "Stock Info" → Analyze
 3. Confirm "Full View" is selected in the view dropdown and all data displays normally
 4. Click "Create View" → check a few fields (e.g., Market Cap, P/E) → name it → Save
 5. Select the new view from the dropdown → confirm only selected fields appear
 6. Switch back to "Full View" → confirm all data reappears
 7. Switch to a different statement type (e.g., Income Statement) → Analyze → confirm the view dropdown shows views for that type only
 8. Delete a view → confirm it's removed from the dropdown
 9. Refresh the page → confirm saved views persist (localStorage)

