#!/usr/bin/env python3
"""Extract French stock tickers from stocks-fr.txt and print yfinance symbols."""

import sys

EXCHANGE_SUFFIX = {
    "XPAR": ".PA",
    "ALXP": ".PA",
    "XMLI": ".PA",
}

def extract(path: str) -> list[str]:
    tickers = []
    with open(path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            code_field = parts[1].strip()          # e.g. "MC XPAR"
            code_parts = code_field.split()
            if len(code_parts) < 2:
                continue
            ticker, exchange = code_parts[0], code_parts[1]
            suffix = EXCHANGE_SUFFIX.get(exchange, ".PA")
            tickers.append(f"{ticker}{suffix}")
    return tickers


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "stocks-fr.txt"
    for t in extract(path):
        print(t)
