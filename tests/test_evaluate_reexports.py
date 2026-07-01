from __future__ import annotations

from core.evaluate import _normalize, _token_f1


def test_evaluate_reexports_normalize():
    assert _normalize(" Hi ", prompt="", cfg={"strip_whitespace": True}) == "hi"


def test_evaluate_reexports_token_f1():
    assert _token_f1("a", "a") == 1.0
