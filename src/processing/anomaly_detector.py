from dataclasses import dataclass
import numpy as np

_EPS = 1e-9 # Tiny number

@dataclass
class AnomalyCheckResult:
    how_many_steps_away: float
    is_unusual: bool
    severity_level: str

def measure_distance_from_normal(today_value: float, past_values: list[float]) -> float:
    # Measures distance from normal in standard deviations: 0 is normal, 2 is high, 3+ is extreme
    if len(past_values) < 2:
        # Insufficient historical data to calculate normal range
        return 0.0

    history = np.array(past_values)
    spread = history.std()

    if spread < _EPS:
        # Any small difference is not meaningful
        return 0.0

    return float((today_value - history.mean())/ spread)

def check_for_health_anomaly(
    today_greenness: float,
    past_greenness_values: list[float],
    moderate_threshold: float = 1.5,
    severe_threshold: float = 2.5,
) -> AnomalyCheckResult:
    # Flags health warnings only for greenness drops, ignoring increases
    steps_away = measure_distance_from_normal(today_greenness, past_greenness_values)
    # A positive number here means health went down
    drop_size = -steps_away 

    if drop_size >= severe_threshold:
        severity = "serve"
    elif drop_size >= moderate_threshold:
        severity = "moderate"
    else:
        severity = "none"

    return AnomalyCheckResult(
        how_many_steps_away=steps_away,
        is_unusual=(severity != "none"),
        severity_level=severity
    )
