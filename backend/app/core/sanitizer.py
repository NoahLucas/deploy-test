from __future__ import annotations

from typing import Dict

ALLOWED_SIGNALS = {
    "sleep_hours": {"min": 0.0, "max": 16.0, "precision": 1},
    "resting_hr": {"min": 35.0, "max": 120.0, "precision": 0},
    "steps": {"min": 0.0, "max": 40000.0, "precision": 0},
    "mindful_minutes": {"min": 0.0, "max": 240.0, "precision": 0},
    "deep_work_minutes": {"min": 0.0, "max": 720.0, "precision": 0},
    "screen_time_hours": {"min": 0.0, "max": 16.0, "precision": 1},
    "vo2_estimate": {"min": 10.0, "max": 80.0, "precision": 1},
}


def sanitize_signals(signals: Dict[str, float]) -> Dict[str, float]:
    sanitized: Dict[str, float] = {}

    for key, value in signals.items():
        rule = ALLOWED_SIGNALS.get(key)
        if rule is None:
            continue

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue

        bounded = max(rule["min"], min(rule["max"], numeric))
        sanitized[key] = round(bounded, int(rule["precision"]))

    return sanitized


def _normalize(value: float, floor: float, ceiling: float) -> float:
    if ceiling <= floor:
        return 0.0
    clipped = max(floor, min(ceiling, value))
    return (clipped - floor) / (ceiling - floor)


def derive_public_scores(signal_averages: Dict[str, float]) -> Dict[str, int]:
    sleep = _normalize(signal_averages.get("sleep_hours", 7.0), 4.0, 9.0)
    resting = 1.0 - _normalize(signal_averages.get("resting_hr", 62.0), 48.0, 85.0)
    mindful = _normalize(signal_averages.get("mindful_minutes", 15.0), 0.0, 60.0)
    steps = _normalize(signal_averages.get("steps", 7000.0), 2000.0, 14000.0)
    deep_work = _normalize(signal_averages.get("deep_work_minutes", 150.0), 30.0, 300.0)
    screen = 1.0 - _normalize(signal_averages.get("screen_time_hours", 7.0), 2.5, 10.5)

    recovery = int(round(100 * ((sleep * 0.45) + (resting * 0.35) + (mindful * 0.2))))
    focus = int(round(100 * ((deep_work * 0.6) + (screen * 0.25) + (mindful * 0.15))))
    balance = int(round(100 * ((steps * 0.35) + (sleep * 0.35) + (screen * 0.3))))

    return {
        "recovery": max(35, min(99, recovery)),
        "focus": max(35, min(99, focus)),
        "balance": max(35, min(99, balance)),
    }


def default_action(scores: Dict[str, int]) -> str:
    recovery = scores.get("recovery", 80)
    focus = scores.get("focus", 80)
    balance = scores.get("balance", 80)

    lowest = min(recovery, focus, balance)

    if lowest == recovery:
        return "Shift one late meeting to protect sleep and recovery range."
    if lowest == focus:
        return "Hold two 90-minute no-message blocks before noon."
    return "Front-load movement breaks to stabilize output through afternoon."


def default_headline(scores: Dict[str, int]) -> str:
    return (
        "Current operating signal: "
        f"recovery {scores['recovery']}/100, focus {scores['focus']}/100, "
        f"balance {scores['balance']}/100."
    )
