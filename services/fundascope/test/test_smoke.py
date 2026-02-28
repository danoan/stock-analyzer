def test_model_imports():
    from fundascope.core.model import METRIC_DEFINITIONS, KEY_METRICS
    assert METRIC_DEFINITIONS
    assert KEY_METRICS

def test_config_defaults():
    from fundascope.utils.config import Config
    cfg = Config()
    assert cfg.api_explorer_url == "http://localhost:8000"
