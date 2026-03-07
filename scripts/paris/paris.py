"""
Euronext Paris stock data CLI.

Commands:
  fetch        — Fetch all listed symbols from Twelve Data API → output/paris_codes.txt
  lookup       — Look up each code via api-explorer → output/paris_lookup_results.json
  filter       — Filter lookup results for EPA exchange symbols → output/paris_symbols.txt
  parse-income — Filter income stmt results for symbols with data → output/paris_income_symbols.txt
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CODES_FILE = OUTPUT_DIR / "paris_codes.txt"
LOOKUP_FILE = OUTPUT_DIR / "paris_lookup_results.json"
EPA_FILE = OUTPUT_DIR / "paris_symbols.txt"
INCOME_SYMBOLS_FILE = OUTPUT_DIR / "paris_income_symbols.txt"

# --- Twelve Data API ---
TWELVE_DATA_URL = "https://api.twelvedata.com/stocks"

# --- Lookup ---
LOOKUP_COUNT = 25             # max results per lookup query
LOOKUP_DELAY = 0.3            # seconds between uncached lookups

# --- Filter ---
FILTER_EXCHANGE = "EPA"


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

def cmd_fetch(_args):
    """Fetch all Euronext Paris symbols from Twelve Data and save to paris_codes.txt."""
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        sys.exit("TWELVE_DATA_API_KEY not set")

    url = f"{TWELVE_DATA_URL}?mic_code=XPAR&apikey={api_key}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())

    symbols = sorted({
        item["symbol"].strip()
        for item in data.get("data", [])
        if item.get("symbol")
    })

    OUTPUT_DIR.mkdir(exist_ok=True)
    CODES_FILE.write_text("\n".join(symbols) + "\n")
    print(f"{len(symbols)} symbols written to {CODES_FILE}")


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def cmd_lookup(_args):
    """Look up each Paris code via api-explorer and save results to paris_lookup_results.json."""
    from api_explorer.core.api import lookup
    from api_explorer.core.model import init_db

    init_db()

    codes = [line.strip() for line in CODES_FILE.read_text().splitlines() if line.strip()]

    try:
        results = json.loads(LOOKUP_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        results = {}

    total = len(codes)
    skipped = 0

    for i, code in enumerate(codes, 1):
        if code in results:
            skipped += 1
            continue

        try:
            data = lookup(code, count=LOOKUP_COUNT)
            results[code] = data["results"]
        except Exception as e:
            print(f"  [{i}/{total}] ERROR {code}: {e}", flush=True)
            results[code] = []
            data = {"from_cache": False}

        LOOKUP_FILE.write_text(json.dumps(results))

        status = "cached" if data.get("from_cache") else "fetched"
        print(f"  [{i}/{total}] {code}: {len(results[code])} results ({status})", flush=True)

        if not data.get("from_cache"):
            time.sleep(LOOKUP_DELAY)

    print(f"\nDone. {len(results)} codes in {LOOKUP_FILE} ({skipped} already cached).")


# ---------------------------------------------------------------------------
# filter
# ---------------------------------------------------------------------------

def cmd_filter(_args):
    """Filter lookup results for EPA exchange symbols and save to paris_symbols.txt."""
    data = json.loads(LOOKUP_FILE.read_text())

    symbols = sorted({
        result["symbol"]
        for results in data.values()
        for result in results
        if result.get("exchange") == FILTER_EXCHANGE
    })

    EPA_FILE.write_text("\n".join(symbols) + "\n")
    print(f"{len(symbols)} EPA symbols written to {EPA_FILE}")


# ---------------------------------------------------------------------------
# parse-income
# ---------------------------------------------------------------------------

def cmd_parse_income(args):
    """Filter income statement results for symbols with at least one row inserted."""
    input_file = Path(args.file)
    symbols = []
    for line in input_file.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip().isdigit() and int(parts[1].strip()) > 0:
            symbols.append(parts[0].strip())
    symbols.sort()
    INCOME_SYMBOLS_FILE.write_text("\n".join(symbols) + "\n")
    print(f"{len(symbols)} symbols with income data written to {INCOME_SYMBOLS_FILE}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Euronext Paris stock data tools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="Fetch all Paris symbols from Twelve Data → output/paris_codes.txt")
    sub.add_parser("lookup", help="Look up each code via api-explorer → output/paris_lookup_results.json")
    sub.add_parser("filter", help="Filter lookup results for EPA symbols → output/paris_symbols.txt")
    p_income = sub.add_parser(
        "parse-income", help="Filter income stmt results → output/paris_income_symbols.txt"
    )
    p_income.add_argument("file", help="Input file (tab-separated: SYMBOL\\tROWS_INSERTED\\t...)")

    args = parser.parse_args()
    {
        "fetch": cmd_fetch,
        "lookup": cmd_lookup,
        "filter": cmd_filter,
        "parse-income": cmd_parse_income,
    }[args.command](args)


if __name__ == "__main__":
    main()
