"""
System Monitor - Performance monitoring tool
"""

import psutil
import time
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Metrics:
    """Performance metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io: Dict
    network_io: Dict


class SystemMonitor:
    """
    System Monitor
    
    Tracks: cpu, memory, disk, network
    """
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.metrics_history = []
    
    def collect_metrics(self) -> Metrics:
        """Collect current system metrics"""
        return Metrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            disk_io=psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
            network_io=psutil.net_io_counters()._asdict()
        )
    
    def start_monitoring(self, duration: int = None):
        """Start continuous monitoring"""
        start_time = time.time()
        
        while True:
            metrics = self.collect_metrics()
            self.metrics_history.append(metrics)
            
            if duration and (time.time() - start_time) >= duration:
                break
            
            time.sleep(self.interval)
    
    def get_stats(self) -> Dict:
        """Get statistical summary"""
        if not self.metrics_history:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        mem_values = [m.memory_percent for m in self.metrics_history]
        
        return {
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": sum(mem_values) / len(mem_values),
                "max": max(mem_values),
                "min": min(mem_values)
            }
        }


if __name__ == "__main__":
    monitor = SystemMonitor()
    print(f"Starting {monitor.__class__.__name__}...")
    
    # Collect for 5 seconds
    monitor.start_monitoring(duration=5)
    
    # Show stats
    stats = monitor.get_stats()
    print(f"\nStats: {stats}")
