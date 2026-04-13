"""FDEBench data models — scoring contract types."""

from ms.common.models.base import FrozenBaseModel


class TaskResolutionResult(FrozenBaseModel):
    """Result from a task-specific resolution scorer."""

    task_id: str
    resolution: float
    dimension_scores: dict[str, float]
    dimension_weights: dict[str, float]
    items_scored: int
    items_errored: int


class EfficiencyResult(FrozenBaseModel):
    """Efficiency score."""

    latency_score: float
    cost_score: float
    efficiency: float
    latency_p50_ms: float
    cost_per_item_usd: float


class RobustnessResult(FrozenBaseModel):
    """Robustness score."""

    adversarial_accuracy: float
    api_resilience: float
    robustness: float
    probes_passed: int
    probes_total: int


class Tier1Score(FrozenBaseModel):
    """Tier 1 score for a single task."""

    task_id: str
    resolution: float
    efficiency: float
    robustness: float
    tier1: float


class FDEBenchComposite(FrozenBaseModel):
    """FDEBench composite score across all tasks."""

    task_scores: list[Tier1Score]
    aggregation: str
    fdebench: float
