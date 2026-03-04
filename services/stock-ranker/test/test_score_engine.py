"""Unit tests for stock_ranker.core.score_engine."""
from __future__ import annotations

import textwrap

import pytest

from stock_ranker.core.score_engine import (
    _apply_grade_map,
    _evaluate_rule,
    evaluate_spec,
    evaluate_threshold_score,
    load_spec_from_str,
    normalize_expression_results,
    score_metric,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SIMPLE_GRADE_MAP = {
    "score_to_grade": [
        {"gte": 4.5, "grade": "A"},
        {"gte": 3.5, "grade": "B"},
        {"gte": 2.5, "grade": "C"},
        {"gte": 1.5, "grade": "D"},
        {"else": True, "grade": "F"},
    ],
    "grade_to_score": {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1},
}

_PE_RULES = [
    {"lt": 0, "score": 1},
    {"lt": 12, "score": 5},
    {"lt": 18, "score": 4},
    {"lt": 25, "score": 3},
    {"lt": 35, "score": 2},
    {"else": True, "score": 1},
]

_PAYOUT_RULES = [
    {"gt": 0, "lte": 0.4, "score": 5},
    {"lte": 0.6, "score": 4},
    {"lte": 0.8, "score": 3},
    {"lte": 1.0, "score": 2},
    {"else": True, "score": 1},
]


# ---------------------------------------------------------------------------
# _evaluate_rule
# ---------------------------------------------------------------------------


def test_evaluate_rule_lt_match():
    assert _evaluate_rule(5.0, {"lt": 10}) is True


def test_evaluate_rule_lt_no_match():
    assert _evaluate_rule(10.0, {"lt": 10}) is False


def test_evaluate_rule_lte_boundary():
    assert _evaluate_rule(10.0, {"lte": 10}) is True
    assert _evaluate_rule(10.001, {"lte": 10}) is False


def test_evaluate_rule_gt_match():
    assert _evaluate_rule(5.0, {"gt": 4}) is True


def test_evaluate_rule_gt_boundary():
    assert _evaluate_rule(4.0, {"gt": 4}) is False


def test_evaluate_rule_gte_boundary():
    assert _evaluate_rule(4.5, {"gte": 4.5}) is True
    assert _evaluate_rule(4.499, {"gte": 4.5}) is False


def test_evaluate_rule_else():
    assert _evaluate_rule(-999.0, {"else": True, "score": 1}) is True


def test_evaluate_rule_multi_operator_and_semantics():
    # 0 < x <= 0.4
    assert _evaluate_rule(0.3, {"gt": 0, "lte": 0.4}) is True
    assert _evaluate_rule(0.0, {"gt": 0, "lte": 0.4}) is False  # not > 0
    assert _evaluate_rule(0.5, {"gt": 0, "lte": 0.4}) is False  # not <= 0.4


# ---------------------------------------------------------------------------
# score_metric — threshold rules
# ---------------------------------------------------------------------------


def test_score_metric_pe_negative():
    assert score_metric(-1.0, _PE_RULES) == 1


def test_score_metric_pe_low():
    assert score_metric(10.0, _PE_RULES) == 5


def test_score_metric_pe_boundary_at_12():
    # lt 12: value=12 does NOT match first score-5 rule, falls to lt 18
    assert score_metric(12.0, _PE_RULES) == 4


def test_score_metric_pe_mid():
    assert score_metric(20.0, _PE_RULES) == 3


def test_score_metric_pe_high():
    assert score_metric(30.0, _PE_RULES) == 2


def test_score_metric_pe_very_high():
    assert score_metric(50.0, _PE_RULES) == 1


def test_score_metric_none_returns_none():
    assert score_metric(None, _PE_RULES) is None


def test_score_metric_nan_returns_none():
    assert score_metric(float("nan"), _PE_RULES) is None


def test_score_metric_inf_returns_none():
    assert score_metric(float("inf"), _PE_RULES) is None


def test_score_metric_bool_returns_none():
    assert score_metric(True, _PE_RULES) is None


def test_score_metric_string_returns_none():
    assert score_metric("high", _PE_RULES) is None


# ---------------------------------------------------------------------------
# payoutRatio compound condition (0 < pr <= 0.4)
# ---------------------------------------------------------------------------


def test_payout_ratio_in_range_scores_5():
    assert score_metric(0.3, _PAYOUT_RULES) == 5


def test_payout_ratio_upper_boundary_of_5():
    assert score_metric(0.4, _PAYOUT_RULES) == 5


def test_payout_ratio_zero_scores_4():
    # pr=0: first rule requires gt 0 (fails); second rule lte 0.6 (matches)
    assert score_metric(0.0, _PAYOUT_RULES) == 4


def test_payout_ratio_negative_scores_4():
    assert score_metric(-0.1, _PAYOUT_RULES) == 4


def test_payout_ratio_mid_range():
    assert score_metric(0.5, _PAYOUT_RULES) == 4
    assert score_metric(0.7, _PAYOUT_RULES) == 3
    assert score_metric(0.9, _PAYOUT_RULES) == 2


def test_payout_ratio_at_1_scores_2():
    assert score_metric(1.0, _PAYOUT_RULES) == 2


def test_payout_ratio_over_1_scores_1():
    assert score_metric(1.5, _PAYOUT_RULES) == 1


# ---------------------------------------------------------------------------
# evaluate_threshold_score
# ---------------------------------------------------------------------------

_VALUATION_DEF = {
    "id": "valuation",
    "label": "Valuation",
    "type": "threshold",
    "aggregate": "mean",
    "metrics": [
        {"key": "trailingPE", "rules": _PE_RULES},
    ],
}

_SPEC_WITH_GRADE_MAP = {"grade_map": _SIMPLE_GRADE_MAP, "scores": []}


def test_evaluate_threshold_score_basic():
    info = {"trailingPE": 10.0}  # score=5 → mean=5.0 → grade A
    result = evaluate_threshold_score(info, _VALUATION_DEF, _SPEC_WITH_GRADE_MAP)
    assert result is not None
    assert result["id"] == "valuation"
    assert result["type"] == "threshold"
    assert result["numeric_score"] == pytest.approx(5.0)
    assert result["grade"] == "A"


def test_evaluate_threshold_score_missing_metric_excluded():
    # No trailingPE → no scores → default 3.0 → grade C
    info: dict = {}
    result = evaluate_threshold_score(info, _VALUATION_DEF, _SPEC_WITH_GRADE_MAP)
    assert result is not None
    assert result["numeric_score"] == pytest.approx(3.0)
    assert result["grade"] == "C"


def test_evaluate_threshold_score_condition_gate_skips():
    _dy_rules = [{"gt": 0.01, "score": 3}, {"else": True, "score": 1}]
    dividends_def = {
        "id": "dividends",
        "label": "Dividends",
        "type": "threshold",
        "aggregate": "mean",
        "condition": {"require_any_truthy": ["dividendYield", "dividendRate"]},
        "metrics": [{"key": "dividendYield", "rules": _dy_rules}],
    }
    # Neither dividendYield nor dividendRate present → should be skipped
    result = evaluate_threshold_score({}, dividends_def, _SPEC_WITH_GRADE_MAP)
    assert result is None


def test_evaluate_threshold_score_condition_gate_passes():
    _dy_rules = [{"gt": 0.01, "score": 3}, {"else": True, "score": 1}]
    dividends_def = {
        "id": "dividends",
        "label": "Dividends",
        "type": "threshold",
        "aggregate": "mean",
        "condition": {"require_any_truthy": ["dividendYield", "dividendRate"]},
        "metrics": [{"key": "dividendYield", "rules": _dy_rules}],
    }
    info = {"dividendYield": 0.03}
    result = evaluate_threshold_score(info, dividends_def, _SPEC_WITH_GRADE_MAP)
    assert result is not None
    assert result["grade"] == "C"  # score=3 → C


def test_evaluate_threshold_score_mean_of_two_metrics():
    _pb_rules = [{"lt": 2, "score": 4}, {"else": True, "score": 2}]
    pe_pb_def = {
        "id": "val",
        "label": "Val",
        "type": "threshold",
        "aggregate": "mean",
        "metrics": [
            {"key": "trailingPE", "rules": _PE_RULES},  # 10 → score 5
            {"key": "priceToBook", "rules": _pb_rules},  # 1 → score 4
        ],
    }
    info = {"trailingPE": 10.0, "priceToBook": 1.0}
    result = evaluate_threshold_score(info, pe_pb_def, _SPEC_WITH_GRADE_MAP)
    assert result is not None
    assert result["numeric_score"] == pytest.approx(4.5)
    assert result["grade"] == "A"  # 4.5 → A


# ---------------------------------------------------------------------------
# _apply_grade_map
# ---------------------------------------------------------------------------


def test_apply_grade_map_boundaries():
    gm = _SIMPLE_GRADE_MAP
    assert _apply_grade_map(5.0, gm) == "A"
    assert _apply_grade_map(4.5, gm) == "A"
    assert _apply_grade_map(4.49, gm) == "B"
    assert _apply_grade_map(3.5, gm) == "B"
    assert _apply_grade_map(3.49, gm) == "C"
    assert _apply_grade_map(2.5, gm) == "C"
    assert _apply_grade_map(2.49, gm) == "D"
    assert _apply_grade_map(1.5, gm) == "D"
    assert _apply_grade_map(1.49, gm) == "F"
    assert _apply_grade_map(1.0, gm) == "F"


# ---------------------------------------------------------------------------
# evaluate_spec — shape and overall_grade
# ---------------------------------------------------------------------------

_SIMPLE_SPEC = {
    "grade_map": _SIMPLE_GRADE_MAP,
    "scores": [
        {
            "id": "valuation",
            "label": "Valuation",
            "type": "threshold",
            "aggregate": "mean",
            "metrics": [{"key": "trailingPE", "rules": _PE_RULES}],
        },
        {
            "id": "profitability",
            "label": "Profitability",
            "type": "threshold",
            "aggregate": "mean",
            "metrics": [
                {
                    "key": "returnOnEquity",
                    "rules": [
                        {"gt": 0.25, "score": 5},
                        {"gt": 0.15, "score": 4},
                        {"gt": 0.08, "score": 3},
                        {"gt": 0, "score": 2},
                        {"else": True, "score": 1},
                    ],
                }
            ],
        },
    ],
}


def test_evaluate_spec_shape():
    info = {"trailingPE": 10.0, "returnOnEquity": 0.30}
    result = evaluate_spec(info, _SIMPLE_SPEC)
    assert "results" in result
    assert "overall_grade" in result
    assert len(result["results"]) == 2
    ids = {r["id"] for r in result["results"]}
    assert ids == {"valuation", "profitability"}


def test_evaluate_spec_overall_grade_computed():
    # trailingPE=10 → score 5 → A; returnOnEquity=0.30 → score 5 → A
    # overall: mean(5,5)=5 → A
    info = {"trailingPE": 10.0, "returnOnEquity": 0.30}
    result = evaluate_spec(info, _SIMPLE_SPEC)
    assert result["overall_grade"] == "A"


def test_evaluate_spec_overall_grade_mixed():
    # trailingPE=20 → score 3 → C; returnOnEquity=-0.05 → score 1 → F
    # overall: mean(3,1)=2 → D
    info = {"trailingPE": 20.0, "returnOnEquity": -0.05}
    result = evaluate_spec(info, _SIMPLE_SPEC)
    assert result["overall_grade"] == "D"


def test_evaluate_spec_skipped_condition_not_in_results():
    spec = {
        "grade_map": _SIMPLE_GRADE_MAP,
        "scores": [
            {
                "id": "dividends",
                "label": "Dividends",
                "type": "threshold",
                "aggregate": "mean",
                "condition": {"require_any_truthy": ["dividendYield"]},
                "metrics": [
                    {
                        "key": "dividendYield",
                        "rules": [{"gt": 0, "score": 3}, {"else": True, "score": 1}],
                    }
                ],
            }
        ],
    }
    result = evaluate_spec({}, spec)
    assert result["results"] == []
    assert result["overall_grade"] == "C"  # fallback with no threshold results


def test_evaluate_spec_expression_score():
    spec = {
        "scores": [
            {
                "id": "value",
                "label": "Value",
                "type": "expression",
                "expression": "pe + eps",
            }
        ]
    }
    info = {"pe": 10.0, "eps": 2.0}
    result = evaluate_spec(info, spec)
    assert len(result["results"]) == 1
    r = result["results"][0]
    assert r["id"] == "value"
    assert r["type"] == "expression"
    assert r["raw_result"] == pytest.approx(12.0)
    assert result["overall_grade"] is None  # no grade_map


# ---------------------------------------------------------------------------
# normalize_expression_results
# ---------------------------------------------------------------------------


def test_normalize_expression_results_basic():
    spec = {"scores": [{"id": "v", "type": "expression", "expression": "pe"}]}
    info_aapl = {"pe": 0.0}
    info_msft = {"pe": 10.0}
    results_by_ticker = {
        "AAPL": evaluate_spec(info_aapl, spec),
        "MSFT": evaluate_spec(info_msft, spec),
    }
    updated = normalize_expression_results(results_by_ticker, "v", "pe")
    aapl_result = next(r for r in updated["AAPL"]["results"] if r["id"] == "v")
    msft_result = next(r for r in updated["MSFT"]["results"] if r["id"] == "v")
    assert aapl_result["result"] == pytest.approx(0.0)
    assert msft_result["result"] == pytest.approx(1.0)
    # raw_result unchanged
    assert aapl_result["raw_result"] == pytest.approx(0.0)
    assert msft_result["raw_result"] == pytest.approx(10.0)


def test_normalize_expression_results_all_same():
    spec = {"scores": [{"id": "v", "type": "expression", "expression": "pe"}]}
    results_by_ticker = {
        "AAPL": evaluate_spec({"pe": 5.0}, spec),
        "MSFT": evaluate_spec({"pe": 5.0}, spec),
    }
    updated = normalize_expression_results(results_by_ticker, "v", "pe")
    for sym in ("AAPL", "MSFT"):
        r = next(x for x in updated[sym]["results"] if x["id"] == "v")
        assert r["result"] == pytest.approx(0.5)


def test_normalize_expression_results_with_none():
    # AAPL has pe missing → raw_result None; MSFT has pe=10.
    # _normalize_values([None, 10.0]): only one non-None value → span=0 → 0.5
    spec = {"scores": [{"id": "v", "type": "expression", "expression": "pe"}]}
    results_by_ticker = {
        "AAPL": evaluate_spec({}, spec),
        "MSFT": evaluate_spec({"pe": 10.0}, spec),
    }
    updated = normalize_expression_results(results_by_ticker, "v", "pe")
    aapl_r = next(x for x in updated["AAPL"]["results"] if x["id"] == "v")
    msft_r = next(x for x in updated["MSFT"]["results"] if x["id"] == "v")
    assert aapl_r["result"] is None
    assert msft_r["result"] == pytest.approx(0.5)  # single non-None value → 0.5


# ---------------------------------------------------------------------------
# Expression scores referencing threshold scores
# ---------------------------------------------------------------------------


def test_expression_score_references_threshold_score():
    """An expression score may use a threshold score's id to reference its numeric_score."""
    spec = {
        "grade_map": _SIMPLE_GRADE_MAP,
        "scores": [
            {
                "id": "valuation",
                "label": "Valuation",
                "type": "threshold",
                "aggregate": "mean",
                "metrics": [{"key": "trailingPE", "rules": _PE_RULES}],
            },
            {
                "id": "composite",
                "label": "Composite",
                "type": "expression",
                # references the threshold score "valuation" by id
                "expression": "valuation * 2",
            },
        ],
    }
    # trailingPE=10 → threshold score 5 → valuation numeric_score=5.0
    # expression: 5.0 * 2 = 10.0
    info = {"trailingPE": 10.0}
    result = evaluate_spec(info, spec)
    assert len(result["results"]) == 2
    threshold_r = next(r for r in result["results"] if r["id"] == "valuation")
    expr_r = next(r for r in result["results"] if r["id"] == "composite")
    assert threshold_r["numeric_score"] == pytest.approx(5.0)
    assert expr_r["raw_result"] == pytest.approx(10.0)
    # "valuation" should appear in variables of the expression result
    assert expr_r["variables"]["valuation"] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# load_spec_from_str validation
# ---------------------------------------------------------------------------


def test_load_spec_from_str_valid():
    yaml_content = textwrap.dedent("""
        scores:
          - type: expression
            id: test
            expression: "pe"
    """)
    spec = load_spec_from_str(yaml_content)
    assert "scores" in spec
    assert len(spec["scores"]) == 1


def test_load_spec_from_str_missing_scores_key():
    with pytest.raises(ValueError, match="'scores'"):
        load_spec_from_str("grade_map: {}")


def test_load_spec_from_str_not_mapping():
    with pytest.raises(ValueError, match="mapping"):
        load_spec_from_str("- item1\n- item2")


def test_load_spec_from_str_scores_not_list():
    with pytest.raises(ValueError, match="list"):
        load_spec_from_str("scores: not_a_list")
