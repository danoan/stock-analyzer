"""Unified scoring engine: evaluates YAML-defined threshold and expression scores."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import yaml
from simpleeval import EvalWithCompoundTypes, NameNotDefined

# ---------------------------------------------------------------------------
# Expression evaluation (extracted from api.py)
# ---------------------------------------------------------------------------

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "log": math.log,
    "sqrt": math.sqrt,
    "exp": math.exp,
}


def _extract_identifiers(expression: str) -> set[str]:
    """Return variable names referenced in an expression, excluding known function names."""
    reserved = set(_ALLOWED_FUNCTIONS.keys()) | {"True", "False", "None"}
    return {m for m in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", expression) if m not in reserved}


def evaluate_expression(expression: str, variables: dict[str, float | None]) -> float | None:
    """Evaluate a mathematical expression with the given variables.

    Returns None if any variable is None/NaN/Inf, or on any evaluation error.
    """
    for v in variables.values():
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None

    evaluator = EvalWithCompoundTypes(
        names=variables,
        functions=_ALLOWED_FUNCTIONS,
    )
    try:
        result = evaluator.eval(expression)
    except (NameNotDefined, Exception):
        return None

    if not isinstance(result, (int, float)):
        return None
    result = float(result)
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def _to_numeric(value: Any) -> float | None:
    """Convert a value to float, returning None for non-numeric types."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    return None


def _normalize_values(values: list[float | None]) -> list[float | None]:
    """Min-max normalize values to [0, 1].

    - None stays None.
    - If all values are None, returns all None.
    - If span == 0, all non-None values become 0.5.
    """
    numeric = [v for v in values if v is not None]
    if not numeric:
        return [None] * len(values)

    vmin = min(numeric)
    vmax = max(numeric)
    span = vmax - vmin

    result: list[float | None] = []
    for v in values:
        if v is None:
            result.append(None)
        elif span == 0:
            result.append(0.5)
        else:
            result.append((v - vmin) / span)
    return result


def _split_additive_terms(expression: str) -> list[str]:
    """Split expression into additive terms at the top level (depth 0)."""
    depth = 0
    split_at: list[int] = []
    for i, c in enumerate(expression):
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c in "+-" and depth == 0 and i > 0:
            split_at.append(i)

    if not split_at:
        return [expression.strip()]

    segments: list[str] = []
    prev = 0
    for pos in split_at:
        seg = expression[prev:pos].strip()
        if seg:
            segments.append(seg)
        prev = pos
    seg = expression[prev:].strip()
    if seg:
        segments.append(seg)
    return segments


def _extract_weight_and_base(term: str) -> tuple[float, str]:
    """Separate a numeric leading coefficient from an additive term."""
    t = term.strip()
    sign = 1.0
    if t.startswith("+"):
        t = t[1:].strip()
    elif t.startswith("-"):
        t = t[1:].strip()
        sign = -1.0

    m = re.match(r"^(\d+(?:\.\d+)?)\s*\*\s*(.+)$", t, re.DOTALL)
    if m:
        coeff = float(m.group(1))
        base = m.group(2).strip()
        if base.startswith("(") and base.endswith(")"):
            base = base[1:-1].strip()
        return sign * coeff, base
    return sign, t


# ---------------------------------------------------------------------------
# Spec loading
# ---------------------------------------------------------------------------


def load_spec(path: str | Path) -> dict:  # type: ignore[type-arg]
    """Load and validate a YAML scoring spec from a file."""
    with open(path) as f:
        spec = yaml.safe_load(f)
    return _validate_spec(spec)


def load_spec_from_str(content: str) -> dict:  # type: ignore[type-arg]
    """Parse and validate a YAML scoring spec from a string."""
    spec = yaml.safe_load(content)
    return _validate_spec(spec)


def _validate_spec(spec: Any) -> dict:  # type: ignore[type-arg]
    if not isinstance(spec, dict):
        raise ValueError("Spec must be a YAML mapping")
    if "scores" not in spec:
        raise ValueError("Spec must have a 'scores' key")
    if not isinstance(spec["scores"], list):
        raise ValueError("'scores' must be a list")
    return spec  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Threshold scoring primitives
# ---------------------------------------------------------------------------


def _evaluate_rule(value: float, rule: dict) -> bool:  # type: ignore[type-arg]
    """Return True if value satisfies all conditions in the rule.

    Supported operators: lt, lte, gt, gte, else. Multiple operators = AND.
    The 'score', 'grade', and 'else' keys are ignored for condition checking
    (except 'else: true' which always matches).
    """
    if rule.get("else"):
        return True
    match = True
    if "lt" in rule and not (value < rule["lt"]):
        match = False
    if "lte" in rule and not (value <= rule["lte"]):
        match = False
    if "gt" in rule and not (value > rule["gt"]):
        match = False
    if "gte" in rule and not (value >= rule["gte"]):
        match = False
    return match


def score_metric(value: Any, rules: list[dict]) -> int | None:  # type: ignore[type-arg]
    """Apply ordered threshold rules to a value. Returns 1–5 or None.

    Returns None if value is missing/NaN/non-numeric (excluded from aggregation).
    Rules are evaluated top-down; first matching rule's score is returned.
    """
    v = _to_numeric(value)
    if v is None:
        return None
    for rule in rules:
        if _evaluate_rule(v, rule):
            score = rule.get("score")
            if score is not None:
                return int(score)
    return None


def _apply_grade_map(numeric_score: float, grade_map: dict) -> str:  # type: ignore[type-arg]
    """Convert a numeric score to a letter grade using the grade_map spec."""
    score_to_grade: list[dict] = grade_map.get("score_to_grade", [])  # type: ignore[assignment]
    for rule in score_to_grade:
        if _evaluate_rule(numeric_score, rule):
            return str(rule["grade"])
    return "C"  # fallback


# ---------------------------------------------------------------------------
# Score evaluation
# ---------------------------------------------------------------------------


def evaluate_threshold_score(
    info: dict,  # type: ignore[type-arg]
    score_def: dict,  # type: ignore[type-arg]
    spec: dict,  # type: ignore[type-arg]
) -> dict | None:  # type: ignore[type-arg]
    """Score all metrics in a threshold score definition and aggregate.

    Returns {id, label, type, numeric_score, grade} or None if the optional
    condition gate fails (e.g. dividends section with no dividend data).
    """
    # Check optional skip condition
    condition = score_def.get("condition")
    if condition:
        require_any_truthy = condition.get("require_any_truthy", [])
        if require_any_truthy and not any(info.get(k) for k in require_any_truthy):
            return None

    metrics: list[dict] = score_def.get("metrics", [])  # type: ignore[assignment]
    aggregate: str = score_def.get("aggregate", "mean")

    scores: list[int] = []
    for metric_def in metrics:
        s = score_metric(info.get(metric_def["key"]), metric_def["rules"])
        if s is not None:
            scores.append(s)

    if not scores:
        numeric_score = 3.0  # default → grade C
    elif aggregate == "mean":
        numeric_score = sum(scores) / len(scores)
    else:
        numeric_score = sum(scores) / len(scores)

    grade_map = spec.get("grade_map")
    grade = _apply_grade_map(numeric_score, grade_map) if grade_map else "C"

    return {
        "id": score_def["id"],
        "label": score_def.get("label", score_def["id"]),
        "type": "threshold",
        "numeric_score": numeric_score,
        "grade": grade,
    }


def evaluate_expression_score(
    info: dict,  # type: ignore[type-arg]
    score_def: dict,  # type: ignore[type-arg]
    score_vars: dict[str, float] | None = None,
) -> dict:  # type: ignore[type-arg]
    """Evaluate an expression score for a single ticker.

    Returns {id, label, type, raw_result, result, variables}.
    score_vars, if provided, contains numeric_score values from preceding
    threshold scores (keyed by score id) so expressions can reference them.
    """
    expression: str = score_def["expression"]
    all_variables: dict[str, float | None] = {k: _to_numeric(v) for k, v in info.items()}
    if score_vars:
        all_variables.update(score_vars)
    referenced = _extract_identifiers(expression)
    expr_variables = {name: all_variables.get(name) for name in referenced}
    raw_result = evaluate_expression(expression, expr_variables)
    return {
        "id": score_def["id"],
        "label": score_def.get("label", score_def["id"]),
        "type": "expression",
        "raw_result": raw_result,
        "result": raw_result,
        "variables": {name: all_variables.get(name) for name in sorted(referenced)},
    }


def evaluate_spec(
    info: dict,  # type: ignore[type-arg]
    spec: dict,  # type: ignore[type-arg]
) -> dict:  # type: ignore[type-arg]
    """Evaluate all scores in a spec against a single ticker's info dict.

    Returns {results: [...], overall_grade: str | None}.
    overall_grade is computed only when threshold scores with grade_map are present.
    """
    results: list[dict] = []  # type: ignore[type-arg]
    score_vars: dict[str, float] = {}
    grade_map = spec.get("grade_map")

    for score_def in spec.get("scores", []):
        score_type = score_def.get("type", "expression")
        if score_type == "threshold":
            result = evaluate_threshold_score(info, score_def, spec)
            if result is not None:
                results.append(result)
                score_vars[score_def["id"]] = result["numeric_score"]
        elif score_type == "expression":
            results.append(evaluate_expression_score(info, score_def, score_vars))

    # Compute overall_grade from threshold results when grade_map is present
    overall_grade: str | None = None
    if grade_map:
        grade_to_score: dict[str, int] = grade_map.get("grade_to_score", {})
        threshold_results = [r for r in results if r.get("type") == "threshold"]
        if threshold_results and grade_to_score:
            grade_scores = [grade_to_score.get(r["grade"], 3) for r in threshold_results]
            avg = sum(grade_scores) / len(grade_scores)
            overall_grade = _apply_grade_map(avg, grade_map)
        elif grade_map:
            overall_grade = "C"  # fallback when no graded sections

    return {"results": results, "overall_grade": overall_grade}


# ---------------------------------------------------------------------------
# Expression normalization across tickers
# ---------------------------------------------------------------------------


def normalize_expression_results(
    results_by_ticker: dict[str, dict],  # type: ignore[type-arg]
    score_id: str,
    expression: str,
) -> dict[str, dict]:  # type: ignore[type-arg]
    """Apply per-term min-max normalization across tickers for an expression score.

    Mirrors the normalization logic in api.py's realize_analysis.
    """
    tickers = list(results_by_ticker.keys())
    terms = _split_additive_terms(expression)

    term_norm_cols: list[list[float | None]] = []
    for term_expr in terms:
        weight, base_expr = _extract_weight_and_base(term_expr)
        term_ids = _extract_identifiers(base_expr)
        term_vals: list[float | None] = []
        for sym in tickers:
            ticker_result = results_by_ticker.get(sym, {})
            score_results: list[dict] = ticker_result.get("results", [])  # type: ignore[assignment]
            score_result = next((r for r in score_results if r.get("id") == score_id), None)
            if score_result is not None:
                vars_dict: dict[str, float | None] = score_result.get("variables", {})
                term_vars = {k: vars_dict.get(k) for k in term_ids}
                val = evaluate_expression(base_expr, term_vars)
            else:
                val = None
            term_vals.append(val)
        normalized = _normalize_values(term_vals)
        term_norm_cols.append([None if v is None else weight * v for v in normalized])

    updated: dict[str, dict] = {}  # type: ignore[type-arg]
    for i, sym in enumerate(tickers):
        ticker_result = results_by_ticker.get(sym, {})
        results_list: list[dict] = ticker_result.get("results", [])  # type: ignore[assignment]
        updated_results: list[dict] = []  # type: ignore[type-arg]
        for r in results_list:
            if r.get("id") == score_id:
                parts = [col[i] for col in term_norm_cols]
                norm_result: float | None = (
                    None if any(p is None for p in parts) else sum(parts)  # type: ignore[arg-type]
                )
                updated_results.append({**r, "result": norm_result})
            else:
                updated_results.append(r)
        updated[sym] = {**ticker_result, "results": updated_results}

    return updated
