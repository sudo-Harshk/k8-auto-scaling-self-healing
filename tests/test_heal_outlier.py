"""Tests for the outlier-pod heal criterion (HEAL_MODE=outlier)."""
from src.decision import decision_engine as de
from src.decision.decision_engine import find_outlier_pod, find_unready_pod


def test_no_outlier_when_pods_similar():
    assert find_outlier_pod({"a": 300.0, "b": 280.0, "c": 310.0}) is None


def test_outlier_detected():
    assert find_outlier_pod({"a": 900.0, "b": 20.0, "c": 25.0}) == "a"


def test_slow_but_below_slo_is_not_outlier():
    # 10x slower than siblings but still under the 250 ms floor
    assert find_outlier_pod({"a": 200.0, "b": 20.0}) is None


def test_single_pod_never_outlier():
    assert find_outlier_pod({"a": 5000.0}) is None


def test_nan_ignored():
    assert find_outlier_pod({"a": 900.0, "b": float("nan"), "c": 30.0}) == "a"


def test_two_pods():
    assert find_outlier_pod({"a": 20.0, "b": 800.0}) == "b"


class _Stub:
    """Minimal engine stub exercising _outlier_heal_candidate."""
    threshold = 0.5

    def __init__(self, series):
        self.series = list(series)
        self.anomaly = self
        self._outlier_pod, self._outlier_streak = None, 0
        self._last_pod_p95, self._last_pod_ready = {}, {}
        self.ready = []

    def _query_pod_p95(self):
        return self.series.pop(0)

    def _query_pod_ready(self):
        return self.ready.pop(0) if self.ready else {}

    _outlier_heal_candidate = de.DecisionEngine._outlier_heal_candidate


def test_persistence_required():
    bad = {"a": 900.0, "b": 20.0}
    s = _Stub([bad, bad])
    assert s._outlier_heal_candidate(0.9) is None      # first window
    assert s._outlier_heal_candidate(0.9) == "a"       # second consecutive window


def test_streak_resets_when_outlier_changes():
    s = _Stub([{"a": 900.0, "b": 20.0}, {"a": 20.0, "b": 900.0}, {"a": 20.0, "b": 900.0}])
    assert s._outlier_heal_candidate(0.9) is None
    assert s._outlier_heal_candidate(0.9) is None      # different pod: streak restarts
    assert s._outlier_heal_candidate(0.9) == "b"


def test_low_anomaly_score_blocks_heal():
    bad = {"a": 900.0, "b": 20.0}
    s = _Stub([bad, bad])
    s._outlier_heal_candidate(0.1)
    assert s._outlier_heal_candidate(0.1) is None


def test_one_heal_per_detection():
    bad = {"a": 900.0, "b": 20.0}
    s = _Stub([bad, bad, bad])
    s._outlier_heal_candidate(0.9)
    assert s._outlier_heal_candidate(0.9) == "a"
    assert s._outlier_heal_candidate(0.9) is None      # needs persistence again


def test_unready_pod_detected_when_sibling_ready():
    assert find_unready_pod({"a": 0.0, "b": 1.0, "c": 1.0}) == "a"


def test_all_unready_is_not_localised():
    assert find_unready_pod({"a": 0.0, "b": 0.0}) is None


def test_all_ready_no_candidate():
    assert find_unready_pod({"a": 1.0, "b": 1.0}) is None


def test_unready_needs_persistence_and_heals_that_pod():
    s = _Stub([{}, {}])
    s.ready = [{"a": 1.0, "b": 0.0}, {"a": 1.0, "b": 0.0}]
    assert s._outlier_heal_candidate(0.9) is None
    assert s._outlier_heal_candidate(0.9) == "b"


def test_gate_none_heals_despite_low_score(monkeypatch):
    monkeypatch.setattr(de, "HEAL_GATE", "none")
    bad = {"a": 900.0, "b": 20.0}
    s = _Stub([bad, bad])
    s._outlier_heal_candidate(0.1)
    assert s._outlier_heal_candidate(0.1) == "a"
