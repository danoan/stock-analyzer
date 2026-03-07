"""
B3 stock data CLI.

Commands:
  fetch   — Fetch all listed company codes from the B3 API → output/b3_codes.txt
  lookup  — Look up each code via api-explorer → output/b3_lookup_results.json
  filter       — Filter lookup results for SAO exchange symbols → output/b3_sao_symbols.txt
  parse-income — Filter income stmt results for symbols with data → output/b3_income_symbols.txt
"""

import argparse
import base64
import json
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
INCOME_SYMBOLS_FILE = OUTPUT_DIR / "b3_income_symbols.txt"
CODES_FILE = OUTPUT_DIR / "b3_codes.txt"
LOOKUP_FILE = OUTPUT_DIR / "b3_lookup_results.json"
SAO_FILE = OUTPUT_DIR / "b3_sao_symbols.txt"

# --- B3 API ---
B3_PAGE_SIZE = 120
B3_FETCH_RETRIES = 5
B3_FETCH_DELAY = 1.5          # seconds between page fetches

# --- Lookup ---
LOOKUP_COUNT = 25             # max results per lookup query
LOOKUP_DELAY = 0.3            # seconds between uncached lookups

# --- Filter ---
FILTER_EXCHANGE = "SAO"


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

def _fetch_page(page: int, page_size: int = B3_PAGE_SIZE, retries: int = B3_FETCH_RETRIES) -> dict:
    params = json.dumps({"language": "pt-br", "pageNumber": page, "pageSize": page_size})
    token = base64.b64encode(params.encode()).decode()
    url = (
        "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy"
        f"/CompanyCall/GetInitialCompanies/{token}"
    )
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.b3.com.br/",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            wait = 4 * (attempt + 1)
            print(f"  Error page {page} attempt {attempt + 1}: {e} — retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch page {page} after {retries} retries")


def cmd_fetch(_args):
    """Fetch all B3 listed company codes and save to b3_codes.txt."""
    all_codes: set[str] = set()
    page = 1
    page_size = B3_PAGE_SIZE

    with open(CODES_FILE, "w") as f:
        while True:
            data = _fetch_page(page, page_size)
            results = data.get("results", [])
            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 1)

            for company in results:
                code = company.get("issuingCompany", "").strip()
                if code:
                    all_codes.add(code)

            f.seek(0)
            f.truncate()
            f.write("\n".join(sorted(all_codes)) + "\n")
            f.flush()

            print(f"Page {page}/{total_pages} saved, total unique codes: {len(all_codes)}", flush=True)

            if page >= total_pages:
                break
            page += 1
            time.sleep(B3_FETCH_DELAY)

    print(f"\nDone. {len(all_codes)} unique codes written to {CODES_FILE}")


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def cmd_lookup(_args):
    """Look up each B3 code via api-explorer and save results to b3_lookup_results.json."""
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
    """Filter lookup results for SAO exchange symbols and save to b3_sao_symbols.txt."""
    data = json.loads(LOOKUP_FILE.read_text())

    sao_symbols = sorted({
        result["symbol"]
        for results in data.values()
        for result in results
        if result.get("exchange") == FILTER_EXCHANGE
    })

    SAO_FILE.write_text("\n".join(sao_symbols) + "\n")
    print(f"{len(sao_symbols)} SAO symbols written to {SAO_FILE}")


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
        description="B3 stock data tools.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="Fetch all B3 listed company codes → output/b3_codes.txt")
    sub.add_parser("lookup", help="Look up each code via api-explorer → output/b3_lookup_results.json")
    sub.add_parser("filter", help="Filter lookup results for SAO symbols → output/b3_sao_symbols.txt")
    p_income = sub.add_parser("parse-income", help="Filter income stmt results → output/b3_income_symbols.txt")
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
