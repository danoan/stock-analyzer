# Extend Score Expression Functions

## Context

Users write score expressions (e.g. `pe * 2 + eps`) evaluated via `simpleeval` against
numeric metrics. The set of allowed functions is defined in `_ALLOWED_FUNCTIONS` in `api.py`.

`exp` is already available (`math.exp`) — no change needed there.

New additions to support penalizing negative values:

- **`sigmoid(x, k=1.0)`** — parameterized sigmoid, maps any real to **(0, 1)**.
  `k` controls steepness: higher `k` = sharper transition near zero.
  - `sigmoid(-0.3, 1)  ≈ 0.43`   (gradual)
  - `sigmoid(-0.3, 10) ≈ 0.05`   (aggressive)
- **`tanh(x)`** — maps to **(-1, 1)**; symmetric, bounded alternative.
- **`log1p(x)`** — `log(1+x)`, numerically stable log for near-zero values.

## Changes

### `src/stock_ranker/core/api.py`

Add a helper before `_ALLOWED_FUNCTIONS`:

```python
def _sigmoid(x: float, k: float = 1.0) -> float:
    """Parameterized sigmoid. k controls steepness (higher k = sharper transition)."""
    return 1.0 / (1.0 + math.exp(-k * x))
```

Update `_ALLOWED_FUNCTIONS`:

```python
_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "log": math.log,
    "log1p": math.log1p,   # log(1+x), numerically stable
    "sqrt": math.sqrt,
    "exp": math.exp,
    "sigmoid": _sigmoid,   # sigmoid(x) or sigmoid(x, k) — penalizes negatives
    "tanh": math.tanh,     # maps to (-1,1)
}
```

### `test/test_core.py`

Add alongside existing `test_evaluate_expression_allowed_functions`:

```python
def test_evaluate_expression_sigmoid_default():
    result = evaluate_expression("sigmoid(a)", {"a": 0.0})
    assert result == pytest.approx(0.5)


def test_evaluate_expression_sigmoid_penalizes_negatives():
    pos = evaluate_expression("sigmoid(a)", {"a": 1.0})
    neg = evaluate_expression("sigmoid(a)", {"a": -1.0})
    assert pos > 0.5
    assert neg < 0.5


def test_evaluate_expression_sigmoid_parameterized():
    # With k=10 the transition is sharp: sigmoid(-0.3, 10) should be well below 0.1
    result = evaluate_expression("sigmoid(a, k)", {"a": -0.3, "k": 10.0})
    assert result < 0.1


def test_evaluate_expression_tanh():
    result = evaluate_expression("tanh(a)", {"a": 0.0})
    assert result == pytest.approx(0.0)


def test_evaluate_expression_log1p():
    result = evaluate_expression("log1p(a)", {"a": 0.0})
    assert result == pytest.approx(0.0)
```

## Verification

```
tox
```
