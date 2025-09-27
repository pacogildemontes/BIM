"""Helper functions for translating raw metrics into scores."""
from __future__ import annotations


def linear_scale(value: float | None, *, minimum: float, maximum: float) -> float:
    """Scale a value between 0 and 100 using linear interpolation."""
    if value is None:
        return 0.0
    if value <= minimum:
        return 0.0
    if value >= maximum:
        return 100.0
    return (value - minimum) / (maximum - minimum) * 100.0


def ramp_scale(value: float | None, *, thresholds: tuple[float, float, float]) -> float:
    """Piecewise scale that guarantees 0/50/100 anchors."""
    if value is None:
        return 0.0
    low, mid, high = thresholds
    if value <= low:
        return 0.0
    if value >= high:
        return 100.0
    if value == mid:
        return 50.0
    if value < mid:
        return 50.0 * (value - low) / (mid - low)
    return 50.0 + 50.0 * (value - mid) / (high - mid)


_CLASSIFICATION_LABELS = [
    (85, "Elite"),
    (70, "Profesional"),
    (55, "Productivo"),
    (40, "Básico"),
    (0, "Limitado"),
]


def classify_index(score: float) -> str:
    """Return the textual classification based on the global score."""
    for threshold, label in _CLASSIFICATION_LABELS:
        if score >= threshold:
            return label
    return "Limitado"
