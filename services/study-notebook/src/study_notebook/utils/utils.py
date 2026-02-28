def truncate(text: str, max_len: int = 40) -> str:
    """Truncate a string to max_len characters, appending '…' if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def fmt_float(value: float | None, precision: int = 4) -> str:
    """Format a float to a fixed number of decimal places, or 'N/A' for None."""
    if value is None:
        return "N/A"
    return f"{value:.{precision}f}"
