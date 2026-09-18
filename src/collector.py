import os
import sys
import time
import json
import psutil
import torch
import numpy as np

def get_disk_usage_percent():
    """Cross-platform disk usage calculation bypassing psutil CPython 3.12 Windows bugs."""
    try:
        if sys.platform == "win32":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\"),
                None,
                ctypes.byref(total_bytes),
                ctypes.byref(free_bytes)
            )
            if total_bytes.value > 0:
                used_bytes = total_bytes.value - free_bytes.value
                return (used_bytes / total_bytes.value) * 100.0
            return 50.0
        else:
            st = os.statvfs('/')
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            return ((total - free) / total) * 100.0 if total > 0 else 50.0
    except Exception:
        return 50.0  # Safe fallback default value

class TelemetryCollector:
    def __init__(self, config_path="config/rules.json"):
        try:
            with open(config_path, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"cpu_threshold": 85.0, "ram_threshold": 85.0}

    def capture_metrics(self):
        """Collects live system metrics."""
        cpu_usage = psutil.cpu_percent(interval=0.5)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = get_disk_usage_percent()
        process_count = len(psutil.pids())
        
        # Simulate log error spike if metrics breach threshold
        error_logs_count = 0 
        if cpu_usage > self.config["cpu_threshold"] or ram_usage > self.config["ram_threshold"]:
            error_logs_count = 2

        return {
            "timestamp": time.time(),
            "cpu_percent": cpu_usage,
            "ram_percent": ram_usage,
            "disk_percent": round(disk_usage, 2),
            "process_count": process_count,
            "error_logs_count": error_logs_count
        }

    def extract_features(self, metrics):
        """Converts raw metrics into a normalized PyTorch tensor."""
        feature_vector = np.array([
            metrics["cpu_percent"] / 100.0,
            metrics["ram_percent"] / 100.0,
            metrics["disk_percent"] / 100.0,
            min(metrics["process_count"] / 1000.0, 1.0),
            min(metrics["error_logs_count"] / 10.0, 1.0)
        ], dtype=np.float32)
        
        return torch.tensor(feature_vector).unsqueeze(0)

if __name__ == "__main__":
    collector = TelemetryCollector()
    raw = collector.capture_metrics()
    print(f"Captured Telemetry:\n{json.dumps(raw, indent=2)}")