from __future__ import annotations

import unicodedata

from core.normalize_answer import drop_prompt_copy, normalize_for_eval


def test_strip_and_lowercase_default():
    out = normalize_for_eval("  Hello World  ", cfg={})
    assert out == "hello world"


def test_drop_copy_removes_prompt_echo():
    prompt = "Answer the question:"
    pred = f"{prompt} Paris"
    out = normalize_for_eval(pred, prompt=prompt, cfg={"drop_copy": True, "drop_eos": True})
    assert out == "paris"


def test_drop_eos_tokens():
    out = normalize_for_eval("done<|eot_id|>", cfg={"drop_eos": True, "lowercase": False})
    assert out == "done"


def test_collapse_whitespace():
    out = normalize_for_eval("a   b\n\tc", cfg={"collapse_whitespace": True})
    assert out == "a b c"


def test_remove_punctuation():
    out = normalize_for_eval("Hello, world!", cfg={"remove_punctuation": True})
    assert out == "hello world"


def test_unicode_nfkc():
    # fullwidth latin letters -> ascii
    src = "\uff41\uff42\uff43"
    out = normalize_for_eval(src, cfg={"unicode_nfkc": True, "lowercase": False})
    assert out == unicodedata.normalize("NFKC", src)


def test_legacy_strip_whitespace_alias():
    out = normalize_for_eval("  X  ", cfg={"strip_whitespace": True, "lowercase": False})
    assert out == "X"


def test_drop_prompt_copy_helper():
    assert drop_prompt_copy("prefix answer", "prefix ", drop_copy=True) == "answer"
