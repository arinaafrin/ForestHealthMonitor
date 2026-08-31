from src.processing.anomaly_detector import (
    measure_distance_from_normal,
    check_for_health_anomaly
)

def test_distance_is_zero_when_not_enough_history():
    # With 0 or 1 past value, we cannot know what "normal" looks like
    assert measure_distance_from_normal(0.5, []) == 0.0
    assert measure_distance_from_normal(0.5, [0.4]) == 0.0

def test_distance_is_zero_when_history_never_changes():
    # If the past values are always the same, a tiny diff means nothing
    assert measure_distance_from_normal(0.5, [0.4, 0.4, 0.4]) == 0.0

def test_big_drop_in_greenness_is_flagged_as_serve():
    healthy_history = [0.70, 0.71, 0.69, 0.72, 0.70]
    result = check_for_health_anomaly(today_greenness=0.30, past_greenness_values=healthy_history)
    assert result.is_unusual is True
    assert result.severity_level == "serve"

def test_normal_value_is_not_flagged():
    healthy_history = [0.70, 0.71, 0.69, 0.72, 0.70]
    result = check_for_health_anomaly(today_greenness=0.705, past_greenness_values=healthy_history)
    assert result.is_unusual is False
    assert result.severity_level == "none"

def test_a_greener_than_unusual_forest_is_not_a_warning():
    # More green is a good thing, so it should never be flagged as unhealthy
    history = [0.40, 0.41, 0.39, 0.40, 0.42]
    result = check_for_health_anomaly(today_greenness=0.90, past_greenness_values=history)
    assert result.is_unusual is False