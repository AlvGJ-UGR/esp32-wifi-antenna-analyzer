"""Wi-Fi Antenna Analyzer — herramientas de PC para el proyecto ESP32.

Submódulos:
    models       Estructuras de datos (NetworkSample, ScanEnd, SecurityType)
    serial_link  Conexión con el ESP32 y parseo del protocolo JSON por línea
    storage      Persistencia de muestras (CSV por ahora, SQLite en el futuro)
    cli          Punto de entrada de consola (waa-scan)
    gui          Interfaz gráfica (waa-gui)
"""

__version__ = "0.2.0"
