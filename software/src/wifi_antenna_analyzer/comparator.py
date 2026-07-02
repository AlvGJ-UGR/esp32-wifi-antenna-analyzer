"""Lógica del Comparador de antenas (Fase 4).

Empareja los resultados de dos benchmarks -uno por antena- por BSSID,
no por SSID: dos redes con el mismo nombre pero distinta MAC (p.ej.
una doble banda 2.4/5GHz, o el vecino con el mismo SSID por defecto
del router) no deben mezclarse entre sí.

Igual que `benchmark.py`, es lógica pura: no sabe nada de GUI, de
ficheros ni de cuándo se corrió cada benchmark. Quien la usa decide
qué dos listas de `BenchmarkResult` comparar.
"""

from __future__ import annotations

from .models import AntennaComparisonRow, BenchmarkResult


def compare_antennas(
    results_a: list[BenchmarkResult],
    results_b: list[BenchmarkResult],
) -> list[AntennaComparisonRow]:
    """Compara dos benchmarks por BSSID.

    Devuelve una fila por cada BSSID visto en cualquiera de los dos
    benchmarks (unión, no intersección), para que las redes que solo
    detectó una de las dos antenas también queden reflejadas con su
    `diff_db` a None.

    Orden: primero las redes detectadas por ambas antenas, de mayor
    a menor diferencia absoluta de RSSI (los casos más interesantes
    para comparar antenas); las redes "solo en A" o "solo en B" van
    al final.
    """
    by_bssid_a = {result.bssid: result for result in results_a}
    by_bssid_b = {result.bssid: result for result in results_b}
    all_bssids = set(by_bssid_a) | set(by_bssid_b)

    rows = []
    for bssid in all_bssids:
        result_a = by_bssid_a.get(bssid)
        result_b = by_bssid_b.get(bssid)
        ssid = (result_a or result_b).ssid  # type: ignore[union-attr]
        rows.append(
            AntennaComparisonRow(
                bssid=bssid,
                ssid=ssid,
                mean_a=result_a.mean if result_a is not None else None,
                mean_b=result_b.mean if result_b is not None else None,
            )
        )

    def sort_key(row: AntennaComparisonRow) -> tuple[int, float]:
        diff = row.diff_db
        if diff is None:
            return (1, 0.0)
        return (0, -abs(diff))

    rows.sort(key=sort_key)
    return rows
