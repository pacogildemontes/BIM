"""Shared dataclasses for benchmark results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SubMetricResult:
    name: str
    value: Optional[float]
    unit: Optional[str]
    score: float
    weight: float
    notes: Optional[str] = None


@dataclass
class ComponentResult:
    name: str
    weight: float
    submetrics: List[SubMetricResult] = field(default_factory=list)

    @property
    def score(self) -> float:
        total_weight = sum(sub.weight for sub in self.submetrics if sub.weight > 0)
        if not total_weight:
            return 0.0
        weighted = sum(sub.score * sub.weight for sub in self.submetrics)
        return weighted / total_weight

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "weight": self.weight,
            "score": self.score,
            "submetrics": [
                {
                    "name": sub.name,
                    "value": sub.value,
                    "unit": sub.unit,
                    "score": sub.score,
                    "weight": sub.weight,
                    "notes": sub.notes,
                }
                for sub in self.submetrics
            ],
        }


@dataclass
class BenchmarkResult:
    components: List[ComponentResult]
    index_score: float
    classification: str
    notes: List[str]
    recommendations: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "index_score": self.index_score,
            "classification": self.classification,
            "components": [component.to_dict() for component in self.components],
            "notes": self.notes,
            "recommendations": self.recommendations,
        }
