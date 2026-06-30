from datetime import datetime

from wifi_antenna_analyzer.benchmark import BenchmarkSession
from wifi_antenna_analyzer.models import NetworkSample, SecurityType


def _sample(bssid: str, rssi: int, ssid: str = "Red") -> NetworkSample:
    return NetworkSample(
        scan_id=1,
        ssid=ssid,
        bssid=bssid,
        rssi=rssi,
        channel=6,
        security=SecurityType.WPA2_PSK,
        timestamp=datetime.now(),
        antenna="dipolo",
    )


def test_benchmark_session_groups_samples_by_bssid_not_ssid():
    session = BenchmarkSession(antenna="dipolo", duration_seconds=10)
    session.add_sample(_sample("AA:BB:CC:DD:EE:01", -60))
    session.add_sample(_sample("AA:BB:CC:DD:EE:01", -62))
    session.add_sample(_sample("AA:BB:CC:DD:EE:02", -70))

    assert session.network_count == 2
    assert session.sample_count == 3

    results = {result.bssid: result for result in session.results()}
    assert results["AA:BB:CC:DD:EE:01"].count == 2
    assert results["AA:BB:CC:DD:EE:02"].count == 1


def test_benchmark_session_results_sorted_by_mean_rssi_desc():
    session = BenchmarkSession(antenna="dipolo", duration_seconds=10)
    session.add_sample(_sample("AA:BB:CC:DD:EE:01", -80, ssid="Lejos"))
    session.add_sample(_sample("AA:BB:CC:DD:EE:02", -50, ssid="Cerca"))
    session.add_sample(_sample("AA:BB:CC:DD:EE:03", -65, ssid="Media"))

    results = session.results()

    assert [result.ssid for result in results] == ["Cerca", "Media", "Lejos"]


def test_benchmark_session_empty_has_no_results():
    session = BenchmarkSession(antenna="dipolo", duration_seconds=10)

    assert session.results() == []
    assert session.network_count == 0
    assert session.sample_count == 0


def test_benchmark_session_keeps_first_ssid_seen_for_a_bssid():
    # Si el SSID cambiase entre muestras de la misma MAC (raro, pero
    # posible con SSIDs ocultos), nos quedamos con el primero visto
    # en vez de sobreescribirlo en cada muestra.
    session = BenchmarkSession(antenna="dipolo", duration_seconds=10)
    session.add_sample(_sample("AA:BB:CC:DD:EE:01", -60, ssid="MiCasa"))
    session.add_sample(_sample("AA:BB:CC:DD:EE:01", -61, ssid="(oculta)"))

    result = session.results()[0]
    assert result.ssid == "MiCasa"
