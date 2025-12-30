"""
JARVIS System Monitor Module
Monitors system resources: CPU, RAM, disk, temperature, network, and processes.
Provides proactive alerts when thresholds are exceeded.
"""

import logging
import threading
import time
import socket
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    """Configurable thresholds for system alerts."""
    cpu_percent: float = 90.0
    cpu_sustained_minutes: int = 5
    ram_percent: float = 85.0
    disk_percent: float = 90.0
    temperature_celsius: float = 80.0


@dataclass
class SystemStatus:
    """Current system status snapshot."""
    cpu_percent: float
    cpu_count: int
    cpu_freq_mhz: Optional[float]
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    ram_available_gb: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    disk_free_gb: float
    temperatures: Dict[str, float] = field(default_factory=dict)
    network_connected: bool = True
    uptime_hours: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str


class SystemMonitor:
    """Monitors system resources and provides alerts."""

    def __init__(
        self,
        thresholds: Optional[AlertThresholds] = None,
        check_interval: float = 30.0,
        on_alert: Optional[Callable[[str], None]] = None
    ):
        self.thresholds = thresholds or AlertThresholds()
        self.check_interval = check_interval
        self.on_alert = on_alert

        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._cpu_history: List[tuple] = []  # (timestamp, cpu_percent)
        self._last_alert_time: Dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=5)

        logger.info("System monitor initialized")

    def start_monitoring(self) -> None:
        """Start background monitoring thread."""
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Background monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Background monitoring stopped")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self._check_for_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

    def _check_for_alerts(self) -> None:
        """Check system status and trigger alerts if needed."""
        status = self.get_status()

        # Track CPU history
        self._cpu_history.append((status.timestamp, status.cpu_percent))
        # Keep only last 15 minutes of history
        cutoff = datetime.now() - timedelta(minutes=15)
        self._cpu_history = [
            (t, c) for t, c in self._cpu_history if t > cutoff
        ]

        # Check sustained high CPU
        if self._is_cpu_sustained_high():
            self._trigger_alert(
                "cpu_sustained",
                f"El CPU lleva {self.thresholds.cpu_sustained_minutes} minutos "
                f"por encima del {self.thresholds.cpu_percent}%"
            )

        # Check RAM
        if status.ram_percent >= self.thresholds.ram_percent:
            self._trigger_alert(
                "ram_high",
                f"La memoria RAM está al {status.ram_percent:.1f}%. "
                f"Quedan {status.ram_available_gb:.1f} GB disponibles"
            )

        # Check disk
        if status.disk_percent >= self.thresholds.disk_percent:
            self._trigger_alert(
                "disk_high",
                f"El disco está al {status.disk_percent:.1f}%. "
                f"Quedan {status.disk_free_gb:.1f} GB libres"
            )

        # Check temperature
        for sensor, temp in status.temperatures.items():
            if temp >= self.thresholds.temperature_celsius:
                self._trigger_alert(
                    f"temp_{sensor}",
                    f"La temperatura de {sensor} está alta: {temp:.1f}°C"
                )

        # Check network
        if not status.network_connected:
            self._trigger_alert(
                "network_down",
                "No hay conexión a internet"
            )

    def _is_cpu_sustained_high(self) -> bool:
        """Check if CPU has been high for sustained period."""
        if not self._cpu_history:
            return False

        cutoff = datetime.now() - timedelta(
            minutes=self.thresholds.cpu_sustained_minutes
        )
        recent = [c for t, c in self._cpu_history if t > cutoff]

        if len(recent) < 3:  # Need at least 3 samples
            return False

        avg = sum(recent) / len(recent)
        return avg >= self.thresholds.cpu_percent

    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """Trigger an alert if not in cooldown."""
        now = datetime.now()
        last_alert = self._last_alert_time.get(alert_type)

        if last_alert and (now - last_alert) < self._alert_cooldown:
            return  # Still in cooldown

        self._last_alert_time[alert_type] = now
        logger.warning(f"Alert: {message}")

        if self.on_alert:
            self.on_alert(f"Señor, {message}")

    def get_status(self) -> SystemStatus:
        """Get current system status."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_mhz = cpu_freq.current if cpu_freq else None

        # Memory
        mem = psutil.virtual_memory()
        ram_total_gb = mem.total / (1024 ** 3)
        ram_used_gb = mem.used / (1024 ** 3)
        ram_available_gb = mem.available / (1024 ** 3)

        # Disk
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)

        # Temperature
        temperatures = self._get_temperatures()

        # Network
        network_connected = self._check_internet()

        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_hours = uptime.total_seconds() / 3600

        return SystemStatus(
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_mhz=cpu_freq_mhz,
            ram_total_gb=ram_total_gb,
            ram_used_gb=ram_used_gb,
            ram_percent=mem.percent,
            ram_available_gb=ram_available_gb,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_percent=disk.percent,
            disk_free_gb=disk_free_gb,
            temperatures=temperatures,
            network_connected=network_connected,
            uptime_hours=uptime_hours,
            timestamp=datetime.now()
        )

    def _get_temperatures(self) -> Dict[str, float]:
        """Get system temperatures if available."""
        temps = {}
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                sensor_temps = psutil.sensors_temperatures()
                if sensor_temps:
                    for name, entries in sensor_temps.items():
                        for entry in entries:
                            label = entry.label or name
                            temps[label] = entry.current
        except Exception as e:
            logger.debug(f"Could not read temperatures: {e}")
        return temps

    def _check_internet(self, timeout: float = 2.0) -> bool:
        """Check internet connectivity."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except OSError:
            return False

    def get_top_processes(
        self,
        by: str = "cpu",
        limit: int = 5
    ) -> List[ProcessInfo]:
        """Get top processes by CPU or memory usage."""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                info = proc.info
                memory_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0

                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    cpu_percent=info['cpu_percent'] or 0,
                    memory_percent=info['memory_percent'] or 0,
                    memory_mb=memory_mb,
                    status=info['status']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by requested metric
        if by == "memory":
            processes.sort(key=lambda p: p.memory_percent, reverse=True)
        else:
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)

        return processes[:limit]

    def get_status_report(self, verbose: bool = False) -> str:
        """Get a human-readable status report."""
        status = self.get_status()
        lines = []

        # Overall status
        if self._is_system_healthy(status):
            lines.append("El sistema está funcionando correctamente.")
        else:
            lines.append("Hay algunas situaciones que requieren atención.")

        lines.append("")

        # CPU
        cpu_status = "normal"
        if status.cpu_percent > 80:
            cpu_status = "alto"
        elif status.cpu_percent > 50:
            cpu_status = "moderado"
        lines.append(f"CPU: {status.cpu_percent:.1f}% ({cpu_status})")

        # RAM
        lines.append(
            f"RAM: {status.ram_used_gb:.1f} GB de {status.ram_total_gb:.1f} GB "
            f"({status.ram_percent:.1f}%)"
        )

        # Disk
        lines.append(
            f"Disco: {status.disk_used_gb:.1f} GB de {status.disk_total_gb:.1f} GB "
            f"({status.disk_percent:.1f}%), {status.disk_free_gb:.1f} GB libres"
        )

        # Temperature
        if status.temperatures:
            max_temp = max(status.temperatures.values())
            lines.append(f"Temperatura: {max_temp:.1f}°C")

        # Network
        network_status = "conectado" if status.network_connected else "sin conexión"
        lines.append(f"Red: {network_status}")

        # Uptime
        hours = int(status.uptime_hours)
        minutes = int((status.uptime_hours - hours) * 60)
        lines.append(f"Tiempo encendido: {hours}h {minutes}m")

        if verbose:
            lines.append("")
            lines.append("Procesos con mayor consumo de CPU:")
            for proc in self.get_top_processes(by="cpu", limit=3):
                lines.append(f"  - {proc.name}: {proc.cpu_percent:.1f}% CPU")

        return "\n".join(lines)

    def get_quick_status(self) -> str:
        """Get a brief status summary for voice response."""
        status = self.get_status()

        if self._is_system_healthy(status):
            return (
                f"Todo en orden. CPU al {status.cpu_percent:.0f}%, "
                f"RAM al {status.ram_percent:.0f}%, "
                f"disco al {status.disk_percent:.0f}%."
            )
        else:
            issues = []
            if status.cpu_percent > 80:
                issues.append(f"CPU alto al {status.cpu_percent:.0f}%")
            if status.ram_percent > 80:
                issues.append(f"RAM alta al {status.ram_percent:.0f}%")
            if status.disk_percent > 85:
                issues.append(f"disco casi lleno al {status.disk_percent:.0f}%")
            if not status.network_connected:
                issues.append("sin conexión a internet")
            for name, temp in status.temperatures.items():
                if temp >= 75:
                    issues.append(f"temperatura {name} a {temp:.0f}°C")

            if issues:
                return "Atención: " + ", ".join(issues) + "."
            else:
                return (
                    f"Sistema estable. CPU al {status.cpu_percent:.0f}%, "
                    f"RAM al {status.ram_percent:.0f}%."
                )

    def _is_system_healthy(self, status: SystemStatus) -> bool:
        """Check if system is in healthy state."""
        return (
            status.cpu_percent < 80 and
            status.ram_percent < 80 and
            status.disk_percent < 85 and
            status.network_connected and
            all(t < 75 for t in status.temperatures.values())
        )

    def get_ram_info(self) -> str:
        """Get RAM information for voice response."""
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)

        return (
            f"Tiene {available_gb:.1f} GB de RAM disponible "
            f"de un total de {total_gb:.1f} GB. "
            f"En uso: {used_gb:.1f} GB ({mem.percent:.0f}%)."
        )

    def get_disk_info(self) -> str:
        """Get disk information for voice response."""
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)

        return (
            f"El disco tiene {free_gb:.1f} GB libres "
            f"de {total_gb:.1f} GB totales ({disk.percent:.0f}% usado)."
        )

    def get_cpu_info(self) -> str:
        """Get CPU information for voice response."""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        info = f"El CPU está al {cpu_percent:.0f}% con {cpu_count} núcleos"
        if cpu_freq:
            info += f" a {cpu_freq.current:.0f} MHz"
        info += "."

        # Add top process if CPU is high
        if cpu_percent > 50:
            top_procs = self.get_top_processes(by="cpu", limit=1)
            if top_procs:
                info += f" El proceso con mayor consumo es {top_procs[0].name}."

        return info

    def get_network_info(self) -> str:
        """Get network information for voice response."""
        if self._check_internet():
            return "La conexión a internet está activa."
        else:
            return "No hay conexión a internet en este momento."


class SystemQueryHandler:
    """Handles system-related queries from user input."""

    # Patterns for system queries
    SYSTEM_PATTERNS = [
        (r"c[oó]mo\s+est[aá]\s+(el\s+)?sistema", "full_status"),
        (r"estado\s+(del\s+)?sistema", "full_status"),
        (r"reporte\s+(del\s+)?sistema", "full_status"),
        (r"cu[aá]nta\s+ram\s+(libre|disponible|tengo)", "ram"),
        (r"memoria\s+(ram|disponible|libre)", "ram"),
        (r"uso\s+de\s+memoria", "ram"),
        (r"cu[aá]nto\s+disco\s+(libre|disponible|queda)", "disk"),
        (r"espacio\s+(en\s+)?disco", "disk"),
        (r"almacenamiento", "disk"),
        (r"c[oó]mo\s+est[aá]\s+(el\s+)?cpu", "cpu"),
        (r"uso\s+(del\s+)?cpu", "cpu"),
        (r"procesador", "cpu"),
        (r"hay\s+internet", "network"),
        (r"conexi[oó]n\s+(a\s+)?(internet|red)", "network"),
        (r"est[aá]\s+conectado", "network"),
        (r"temperatura", "temperature"),
        (r"qu[eé]\s+procesos", "processes"),
        (r"qu[eé]\s+est[aá]\s+consumiendo", "processes"),
    ]

    def __init__(self, monitor: Optional[SystemMonitor] = None):
        self.monitor = monitor or SystemMonitor()

    def process_query(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Process a system-related query.

        Returns:
            Tuple of (was_system_query, response)
        """
        input_lower = user_input.lower().strip()

        for pattern, query_type in self.SYSTEM_PATTERNS:
            if re.search(pattern, input_lower):
                response = self._handle_query(query_type)
                return (True, response)

        return (False, None)

    def _handle_query(self, query_type: str) -> str:
        """Handle a specific query type."""
        handlers = {
            "full_status": self.monitor.get_quick_status,
            "ram": self.monitor.get_ram_info,
            "disk": self.monitor.get_disk_info,
            "cpu": self.monitor.get_cpu_info,
            "network": self.monitor.get_network_info,
            "temperature": self._get_temperature_info,
            "processes": self._get_processes_info,
        }

        handler = handlers.get(query_type, self.monitor.get_quick_status)
        return handler()

    def _get_temperature_info(self) -> str:
        """Get temperature information."""
        status = self.monitor.get_status()
        if status.temperatures:
            temps = [f"{name}: {temp:.0f}°C"
                    for name, temp in status.temperatures.items()]
            return "Temperaturas del sistema: " + ", ".join(temps[:3]) + "."
        else:
            return "No puedo acceder a los sensores de temperatura."

    def _get_processes_info(self) -> str:
        """Get top processes information."""
        procs = self.monitor.get_top_processes(by="cpu", limit=3)
        if procs:
            lines = ["Los procesos con mayor consumo son:"]
            for p in procs:
                lines.append(f"{p.name}: {p.cpu_percent:.0f}% CPU, {p.memory_mb:.0f} MB RAM")
            return " ".join(lines)
        else:
            return "No puedo obtener información de los procesos."


# Singleton instances
_monitor_instance: Optional[SystemMonitor] = None
_query_handler_instance: Optional[SystemQueryHandler] = None


def get_system_monitor(
    thresholds: Optional[AlertThresholds] = None,
    on_alert: Optional[Callable[[str], None]] = None
) -> SystemMonitor:
    """Get or create the system monitor instance."""
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = SystemMonitor(
            thresholds=thresholds,
            on_alert=on_alert
        )

    return _monitor_instance


def get_query_handler() -> SystemQueryHandler:
    """Get or create the query handler instance."""
    global _query_handler_instance

    if _query_handler_instance is None:
        _query_handler_instance = SystemQueryHandler(get_system_monitor())

    return _query_handler_instance
