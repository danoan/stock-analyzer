import httpx


def fetch_data(
    api_url: str,
    ticker: str,
    method: str,
    force_refresh: bool = False,
    period: str | None = None,
) -> dict:
    """Call api-explorer POST /api/data/json and return the payload dict."""
    url = f"{api_url.rstrip('/')}/api/data/json"
    payload: dict = {"ticker": ticker, "method": method, "force_refresh": force_refresh}
    if period is not None:
        payload["period"] = period
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()["data"]
    if data.get("type") == "error":
        raise ValueError(data.get("message") or "api error")
    return data
