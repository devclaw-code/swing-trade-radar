"""Tests for `_sanitize_verdict_payload` — strips internal dev notes from stored
verdicts before they are served, without mutating the input payload.
"""

from __future__ import annotations

import copy

import pytest

from swing_trader.engine.signal_generator import (
    _CLEAN_EARNINGS_NOTE,
    _sanitize_verdict_payload,
)


def _payload_with_note(note: str) -> dict:
    return {
        "ticker": "NVDA",
        "why": {
            "evidence": [
                {"label": "earnings", "note": note},
                {"label": "trend", "note": "Above 50/200 SMA."},
            ]
        },
    }


@pytest.mark.parametrize(
    "dirty_note",
    [
        "TODO: wire yfinance earnings here",
        "devclaw left this stub",
        "wire yfinance before ship",
        "calendar unavailable — gate skipped",
        "GATE SKIPPED for now",  # case-insensitive
    ],
)
def test_dev_notes_are_scrubbed(dirty_note: str) -> None:
    out = _sanitize_verdict_payload(_payload_with_note(dirty_note))
    notes = [e["note"] for e in out["why"]["evidence"]]
    assert _CLEAN_EARNINGS_NOTE in notes
    assert dirty_note not in notes
    # The clean sibling note must survive untouched.
    assert "Above 50/200 SMA." in notes


def test_clean_note_passes_through_unchanged() -> None:
    clean = _payload_with_note("Earnings confirmed 2026-07-01, outside hold window.")
    out = _sanitize_verdict_payload(clean)
    assert out == clean
    assert out["why"]["evidence"][0]["note"].startswith("Earnings confirmed")


def test_input_payload_is_not_mutated() -> None:
    original = _payload_with_note("TODO: devclaw remove this")
    snapshot = copy.deepcopy(original)
    out = _sanitize_verdict_payload(original)
    # Caller's object is untouched (cache-safety guarantee)...
    assert original == snapshot
    # ...and the returned copy is genuinely sanitized + distinct.
    assert out is not original
    assert out["why"]["evidence"][0]["note"] == _CLEAN_EARNINGS_NOTE


@pytest.mark.parametrize("not_a_dict", [None, "string", 42, ["list"], 3.14])
def test_non_dict_payload_returned_as_is(not_a_dict: object) -> None:
    assert _sanitize_verdict_payload(not_a_dict) is not_a_dict  # type: ignore[arg-type]


def test_missing_or_malformed_why_is_safe() -> None:
    # No "why" key at all.
    assert _sanitize_verdict_payload({"ticker": "AAPL"}) == {"ticker": "AAPL"}
    # "why" present but not a dict.
    assert _sanitize_verdict_payload({"why": "nope"}) == {"why": "nope"}
    # evidence not a list.
    assert _sanitize_verdict_payload({"why": {"evidence": {}}}) == {"why": {"evidence": {}}}
    # evidence item not a dict / note not a str.
    weird = {"why": {"evidence": ["x", {"note": 123}, {"label": "no-note"}]}}
    assert _sanitize_verdict_payload(weird) == weird
