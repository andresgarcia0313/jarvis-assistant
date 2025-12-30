"""
Tests for JARVIS System Monitor module.
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestSystemMonitor:
    """Tests for SystemMonitor class."""

    def test_initialization(self):
        """Test monitor initialization."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        assert monitor.thresholds is not None
        assert monitor.check_interval == 30.0

    def test_initialization_with_custom_thresholds(self):
        """Test monitor with custom thresholds."""
        from modules.system_monitor import SystemMonitor, AlertThresholds

        thresholds = AlertThresholds(
            cpu_percent=80.0,
            ram_percent=70.0,
            disk_percent=85.0
        )
        monitor = SystemMonitor(thresholds=thresholds)

        assert monitor.thresholds.cpu_percent == 80.0
        assert monitor.thresholds.ram_percent == 70.0

    def test_get_status(self):
        """Test getting system status."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        status = monitor.get_status()

        assert status.cpu_percent >= 0
        assert status.cpu_count > 0
        assert status.ram_total_gb > 0
        assert status.ram_percent >= 0
        assert status.disk_total_gb > 0
        assert isinstance(status.network_connected, bool)

    def test_get_status_report(self):
        """Test getting status report."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        report = monitor.get_status_report()

        assert len(report) > 0
        assert "CPU" in report
        assert "RAM" in report
        assert "Disco" in report

    def test_get_quick_status(self):
        """Test getting quick status."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        status = monitor.get_quick_status()

        assert len(status) > 0
        # Should contain useful status info (percentage or temperature)
        assert "%" in status or "°C" in status or "internet" in status

    def test_get_ram_info(self):
        """Test getting RAM info."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        info = monitor.get_ram_info()

        assert "GB" in info
        assert "RAM" in info or "disponible" in info

    def test_get_disk_info(self):
        """Test getting disk info."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        info = monitor.get_disk_info()

        assert "GB" in info
        assert "disco" in info.lower()

    def test_get_cpu_info(self):
        """Test getting CPU info."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        info = monitor.get_cpu_info()

        assert "CPU" in info
        assert "%" in info

    def test_get_network_info(self):
        """Test getting network info."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        info = monitor.get_network_info()

        assert "conexión" in info.lower() or "internet" in info.lower()

    def test_get_top_processes(self):
        """Test getting top processes."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        procs = monitor.get_top_processes(limit=5)

        assert len(procs) <= 5
        if procs:
            assert procs[0].pid > 0
            assert procs[0].name is not None

    def test_get_top_processes_by_memory(self):
        """Test getting top processes by memory."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        procs = monitor.get_top_processes(by="memory", limit=3)

        assert len(procs) <= 3

    def test_start_stop_monitoring(self):
        """Test starting and stopping background monitoring."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor(check_interval=0.1)

        monitor.start_monitoring()
        assert monitor._running

        time.sleep(0.2)

        monitor.stop_monitoring()
        assert not monitor._running

    def test_alert_callback(self):
        """Test alert callback is called."""
        from modules.system_monitor import SystemMonitor, AlertThresholds

        alerts = []

        def on_alert(msg):
            alerts.append(msg)

        # Set very low thresholds to trigger alerts
        thresholds = AlertThresholds(
            cpu_percent=0.0,  # Will always trigger
            ram_percent=0.0,
            disk_percent=0.0
        )

        monitor = SystemMonitor(
            thresholds=thresholds,
            check_interval=0.1,
            on_alert=on_alert
        )

        # Manually trigger check
        monitor._check_for_alerts()

        # Should have triggered at least one alert
        assert len(alerts) > 0

    def test_alert_cooldown(self):
        """Test alert cooldown prevents spam."""
        from modules.system_monitor import SystemMonitor, AlertThresholds
        from datetime import timedelta

        alerts = []

        thresholds = AlertThresholds(ram_percent=0.0)
        monitor = SystemMonitor(
            thresholds=thresholds,
            on_alert=lambda m: alerts.append(m)
        )
        monitor._alert_cooldown = timedelta(seconds=10)

        # Trigger twice
        monitor._check_for_alerts()
        initial_count = len(alerts)

        monitor._check_for_alerts()

        # Second should be blocked by cooldown
        assert len(alerts) == initial_count


class TestSystemQueryHandler:
    """Tests for SystemQueryHandler class."""

    def test_initialization(self):
        """Test query handler initialization."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()
        assert handler.monitor is not None

    def test_system_status_query(self):
        """Test system status query."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "cómo está el sistema",
            "como esta el sistema",
            "estado del sistema",
            "reporte del sistema",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"
            assert response is not None

    def test_ram_query(self):
        """Test RAM queries."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "cuánta RAM libre tengo",
            "cuanta ram disponible",
            "memoria RAM",
            "uso de memoria",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"
            assert "GB" in response

    def test_disk_query(self):
        """Test disk queries."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "cuánto disco libre",
            "espacio en disco",
            "almacenamiento",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"
            assert "GB" in response or "disco" in response.lower()

    def test_cpu_query(self):
        """Test CPU queries."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "cómo está el CPU",
            "uso del cpu",
            "procesador",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"
            assert "CPU" in response or "%" in response

    def test_network_query(self):
        """Test network queries."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "hay internet",
            "conexión a internet",
            "está conectado",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"
            assert "conexión" in response.lower() or "internet" in response.lower()

    def test_processes_query(self):
        """Test processes query."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "qué procesos",
            "qué está consumiendo",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert is_query, f"Should recognize: {query}"

    def test_non_system_query(self):
        """Test non-system queries pass through."""
        from modules.system_monitor import SystemQueryHandler

        handler = SystemQueryHandler()

        queries = [
            "qué hora es",
            "cuéntame un chiste",
            "hola jarvis",
        ]

        for query in queries:
            is_query, response = handler.process_query(query)
            assert not is_query, f"Should not recognize: {query}"
            assert response is None


class TestAlertThresholds:
    """Tests for AlertThresholds dataclass."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        from modules.system_monitor import AlertThresholds

        thresholds = AlertThresholds()

        assert thresholds.cpu_percent == 90.0
        assert thresholds.ram_percent == 85.0
        assert thresholds.disk_percent == 90.0
        assert thresholds.temperature_celsius == 80.0

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        from modules.system_monitor import AlertThresholds

        thresholds = AlertThresholds(
            cpu_percent=75.0,
            ram_percent=80.0,
            disk_percent=95.0
        )

        assert thresholds.cpu_percent == 75.0
        assert thresholds.ram_percent == 80.0
        assert thresholds.disk_percent == 95.0


class TestSystemStatus:
    """Tests for SystemStatus dataclass."""

    def test_status_creation(self):
        """Test creating a status object."""
        from modules.system_monitor import SystemStatus

        status = SystemStatus(
            cpu_percent=50.0,
            cpu_count=8,
            cpu_freq_mhz=3000.0,
            ram_total_gb=16.0,
            ram_used_gb=8.0,
            ram_percent=50.0,
            ram_available_gb=8.0,
            disk_total_gb=500.0,
            disk_used_gb=250.0,
            disk_percent=50.0,
            disk_free_gb=250.0,
            network_connected=True,
            uptime_hours=24.0
        )

        assert status.cpu_percent == 50.0
        assert status.ram_total_gb == 16.0
        assert status.network_connected


class TestProcessInfo:
    """Tests for ProcessInfo dataclass."""

    def test_process_info_creation(self):
        """Test creating a process info object."""
        from modules.system_monitor import ProcessInfo

        proc = ProcessInfo(
            pid=1234,
            name="python",
            cpu_percent=10.5,
            memory_percent=2.3,
            memory_mb=256.0,
            status="running"
        )

        assert proc.pid == 1234
        assert proc.name == "python"
        assert proc.cpu_percent == 10.5


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_system_monitor(self):
        """Test get_system_monitor returns instance."""
        from modules import system_monitor as sm

        # Reset singleton
        sm._monitor_instance = None

        monitor = sm.get_system_monitor()
        assert monitor is not None

    def test_get_query_handler(self):
        """Test get_query_handler returns instance."""
        from modules import system_monitor as sm

        # Reset singletons
        sm._monitor_instance = None
        sm._query_handler_instance = None

        handler = sm.get_query_handler()
        assert handler is not None


class TestInternetCheck:
    """Tests for internet connectivity check."""

    def test_check_internet_with_connection(self):
        """Test internet check when connected."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        # This test assumes the machine has internet
        # In CI without internet, this would fail
        result = monitor._check_internet(timeout=1.0)
        assert isinstance(result, bool)

    @patch('socket.create_connection')
    def test_check_internet_timeout(self, mock_socket):
        """Test internet check handles timeout."""
        from modules.system_monitor import SystemMonitor
        import socket

        mock_socket.side_effect = socket.timeout()

        monitor = SystemMonitor()
        result = monitor._check_internet(timeout=0.1)
        assert result is False

    @patch('socket.create_connection')
    def test_check_internet_no_connection(self, mock_socket):
        """Test internet check when disconnected."""
        from modules.system_monitor import SystemMonitor

        mock_socket.side_effect = OSError()

        monitor = SystemMonitor()
        result = monitor._check_internet()
        assert result is False


class TestTemperatureReading:
    """Tests for temperature reading."""

    def test_get_temperatures(self):
        """Test temperature reading."""
        from modules.system_monitor import SystemMonitor

        monitor = SystemMonitor()
        temps = monitor._get_temperatures()

        # Temperatures might be empty on some systems
        assert isinstance(temps, dict)

    @patch('psutil.sensors_temperatures')
    def test_get_temperatures_with_sensors(self, mock_temps):
        """Test temperature reading with mock sensors."""
        from modules.system_monitor import SystemMonitor

        mock_entry = MagicMock()
        mock_entry.label = "CPU"
        mock_entry.current = 55.0

        mock_temps.return_value = {"coretemp": [mock_entry]}

        monitor = SystemMonitor()
        temps = monitor._get_temperatures()

        assert "CPU" in temps
        assert temps["CPU"] == 55.0
