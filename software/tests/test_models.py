from datetime import datetime

import pytest

from wifi_antenna_analyzer.models import BenchmarkResult, NetworkSample, SecurityType


def test_security_type_from_known_code():
    assert SecurityType.from_code(3) is SecurityType.WPA2_PSK


def test_security_type_from_unknown_code_returns_none():
    assert SecurityType.from_code(99) is None


def test_security_type_from_none_returns_none():
    assert SecurityType.from_code(None) is None


def test_network_sample_security_name_unknown():
    sample = NetworkSample(
        scan_id=1,
        ssid="Test",
        bssid="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        channel=6,
        security=None,
        timestamp=datetime.now(),
    )
    assert sample.security_name == "UNKNOWN"


def test_network_sample_security_name_known():
    sample = NetworkSample(
        scan_id=1,
        ssid="Test",
        bssid="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        channel=6,
        security=SecurityType.WPA2_PSK,
        timestamp=datetime.now(),
    )
    assert sample.security_name == "WPA2_PSK"


def test_benchmark_result_aggregates():
    result = BenchmarkResult(bssid="AA:BB:CC:DD:EE:FF", ssid="Test", antenna="dipolo")
    for rssi in (-60, -65, -55):
        result.add_sample(rssi)

    assert result.count == 3
    assert result.minimum == -65
    assert result.maximum == -55
    assert result.mean == -60.0


def test_benchmark_result_empty_has_none_stats():
    result = BenchmarkResult(bssid="AA:BB:CC:DD:EE:FF", ssid="Test", antenna="dipolo")
    assert result.mean is None
    assert result.minimum is None
    assert result.maximum is None
    assert result.stdev is None


def test_benchmark_result_stdev_single_sample_is_zero():
    result = BenchmarkResult(bssid="AA:BB:CC:DD:EE:FF", ssid="Test", antenna="dipolo")
    result.add_sample(-60)
    assert result.stdev == 0.0


def test_benchmark_result_stdev_multiple_samples():
    result = BenchmarkResult(bssid="AA:BB:CC:DD:EE:FF", ssid="Test", antenna="dipolo")
    for rssi in (-60, -62, -58):
        result.add_sample(rssi)
    assert result.stdev == pytest.approx(2.0, abs=0.01)
