import csv
from datetime import datetime

from wifi_antenna_analyzer.models import BenchmarkResult, NetworkSample, SecurityType
from wifi_antenna_analyzer.storage import BenchmarkCsvWriter, ScanCsvWriter


def test_csv_writer_creates_file_with_header(tmp_path):
    writer = ScanCsvWriter(outdir=tmp_path, antenna="dipolo 5dbi")
    writer.close()

    assert writer.path.exists()
    assert writer.path.parent == tmp_path
    assert "dipolo_5dbi" in writer.path.name  # los espacios se normalizan

    with writer.path.open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == ScanCsvWriter.FIELDNAMES


def test_csv_writer_writes_sample_row(tmp_path):
    sample = NetworkSample(
        scan_id=1,
        ssid="MiCasa",
        bssid="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        channel=6,
        security=SecurityType.WPA2_PSK,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        antenna="dipolo",
    )

    writer = ScanCsvWriter(outdir=tmp_path, antenna="dipolo")
    writer.write(sample)
    writer.close()

    with writer.path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]
    assert row["ssid"] == "MiCasa"
    assert row["mac"] == "AA:BB:CC:DD:EE:FF"
    assert row["rssi"] == "-60"
    assert row["security"] == "WPA2_PSK"
    assert row["fecha"] == "2024-01-01"


def test_benchmark_csv_writer_creates_file_with_header(tmp_path):
    writer = BenchmarkCsvWriter(outdir=tmp_path, antenna="dipolo 5dbi")
    writer.close()

    assert writer.path.exists()
    assert "benchmark_" in writer.path.name
    assert "dipolo_5dbi" in writer.path.name

    with writer.path.open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == BenchmarkCsvWriter.FIELDNAMES


def test_benchmark_csv_writer_writes_result_rows(tmp_path):
    result = BenchmarkResult(bssid="AA:BB:CC:DD:EE:FF", ssid="MiCasa", antenna="dipolo")
    for rssi in (-60, -62, -58):
        result.add_sample(rssi)

    writer = BenchmarkCsvWriter(outdir=tmp_path, antenna="dipolo")
    writer.write_results([result])
    writer.close()

    with writer.path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]
    assert row["ssid"] == "MiCasa"
    assert row["mac"] == "AA:BB:CC:DD:EE:FF"
    assert row["muestras"] == "3"
    assert row["rssi_medio"] == "-60.00"
    assert row["rssi_min"] == "-62"
    assert row["rssi_max"] == "-58"


def test_benchmark_csv_writer_handles_empty_results(tmp_path):
    writer = BenchmarkCsvWriter(outdir=tmp_path, antenna="dipolo")
    writer.write_results([])
    writer.close()

    with writer.path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == []
