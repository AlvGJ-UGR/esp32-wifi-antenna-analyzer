from wifi_antenna_analyzer.models import NetworkSample, ScanEnd
from wifi_antenna_analyzer.serial_link import SerialLink


def test_parse_line_network_sample():
    line = (
        '{"scan":145,"ssid":"MiCasa","mac":"C8:3A:35:45:AA:90",'
        '"rssi":-61,"channel":6,"security":3}'
    )
    event = SerialLink.parse_line(line, antenna="dipolo_5dbi")

    assert isinstance(event, NetworkSample)
    assert event.scan_id == 145
    assert event.ssid == "MiCasa"
    assert event.bssid == "C8:3A:35:45:AA:90"
    assert event.rssi == -61
    assert event.channel == 6
    assert event.security_name == "WPA2_PSK"
    assert event.antenna == "dipolo_5dbi"


def test_parse_line_scan_end():
    line = '{"scan":145,"event":"scan_end","count":24}'
    event = SerialLink.parse_line(line)

    assert isinstance(event, ScanEnd)
    assert event.scan_id == 145
    assert event.network_count == 24


def test_parse_line_hidden_ssid_falls_back_to_placeholder():
    line = '{"scan":1,"ssid":"","mac":"AA:BB:CC:DD:EE:FF","rssi":-70,"channel":1,"security":0}'
    event = SerialLink.parse_line(line)

    assert isinstance(event, NetworkSample)
    assert event.ssid == "(oculta)"


def test_parse_line_invalid_json_returns_none():
    assert SerialLink.parse_line("esto no es json") is None


def test_parse_line_incomplete_json_returns_none():
    assert SerialLink.parse_line('{"scan":1,"ssid":"Test"}') is None


def test_parse_line_unknown_security_code_is_handled_gracefully():
    line = '{"scan":1,"ssid":"Test","mac":"AA:BB:CC:DD:EE:FF","rssi":-50,"channel":1,"security":99}'
    event = SerialLink.parse_line(line)

    assert isinstance(event, NetworkSample)
    assert event.security_name == "UNKNOWN"
