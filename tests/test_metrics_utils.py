from __future__ import annotations

from core.metrics_utils import (
    dialogue_slot_error_rate,
    lcs_overlap,
    parse_dialogue_act_values,
    rouge_l_fscore,
    sentence_bleu4,
    starts_incorrectly,
    token_f1,
)


def test_token_f1_exact_match():
    assert token_f1("a b c", "a b c") == 1.0


def test_token_f1_disjoint():
    assert token_f1("a", "b") == 0.0


def test_token_f1_partial_overlap():
    f1 = token_f1("a b", "a c")
    assert 0.0 < f1 < 1.0


def test_lcs_overlap_full():
    assert lcs_overlap("a b c", "a b c") == 1.0


def test_rouge_l_identical():
    assert rouge_l_fscore("a b", "a b") == 1.0


def test_bleu_identical():
    assert sentence_bleu4("a b c", "a b c") == 1.0


def test_starts_incorrectly():
    assert starts_incorrectly("x y z", "a b c") is True
    assert starts_incorrectly("a b c", "a b c") is False


def test_parse_dialogue_act_values_filters_non_entities():
    values = parse_dialogue_act_values('restaurant_inform(name="Kymmoy",area="centre",none="none")')
    assert values == ["kymmoy", "centre"]


def test_dialogue_slot_error_rate_missing_values():
    act = 'booking_book(name="kymmoy",ref="TQVKVLNH")'
    assert dialogue_slot_error_rate(act, "Booked kymmoy for you.") == 0.5


def test_dialogue_slot_error_rate_no_slots():
    assert dialogue_slot_error_rate("booking_nobook() ", "Sorry, no booking is available.") is None
