"""Load testing configuration and scenarios for Windows-AI.

Uses Locust for load testing to identify performance bottlenecks,
measure response times, and establish performance baselines.
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import logging
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LoadTestStats:
    """Track and report load test statistics."""

    def __init__(self):
        """Initialize statistics tracker."""
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        if not self.response_times:
            return {
                "duration_seconds": 0,
                "total_requests": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0,
            }

        self.response_times.sort()
        n = len(self.response_times)
        return {
            "duration_seconds": (self.end_time - self.start_time) if self.start_time and self.end_time else 0,
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "min_response_ms": min(self.response_times),
            "max_response_ms": max(self.response_times),
            "avg_response_ms": sum(self.response_times) / n,
            "p50_response_ms": self.response_times[n // 2],
            "p95_response_ms": self.response_times[int(n * 0.95)],
            "p99_response_ms": self.response_times[int(n * 0.99)],
            "rps": self.total_requests / ((self.end_time - self.start_time) if self.start_time and self.end_time and (self.end_time - self.start_time) > 0 else 1),
        }


# Global stats tracker
load_test_stats = LoadTestStats()


class APIUser(FastHttpUser):
    """Simulates regular API users."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    task_weight = 60  # 60% of traffic

    @task(10)
    def list_plugins(self):
        """List all available plugins."""
        response = self.client.get("/api/v1/plugins")
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)

    @task(8)
    def get_plugin_info(self):
        """Get information about a specific plugin."""
        plugin_id = "webhook_handler"  # Use a known plugin
        response = self.client.get(f"/api/v1/plugins/{plugin_id}")
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)

    @task(5)
    def search_plugins(self):
        """Search for plugins."""
        response = self.client.get(
            "/api/v1/plugins/search",
            params={"q": "handler", "limit": 10}
        )
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)

    @task(3)
    def health_check(self):
        """Check API health."""
        response = self.client.get("/health")
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)


class HeavyAPIUser(FastHttpUser):
    """Simulates power users with heavy API usage."""

    wait_time = between(0.1, 1)  # Wait 100ms-1s between requests
    task_weight = 30  # 30% of traffic

    @task(15)
    def batch_operation(self):
        """Simulate batch operations."""
        payload = {
            "operations": [
                {"type": "list", "resource": "plugins"},
                {"type": "get", "resource": "plugin", "id": "webhook_handler"},
                {"type": "search", "query": "data"},
            ]
        }
        response = self.client.post(
            "/api/v1/batch",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)

    @task(10)
    def plugin_execution(self):
        """Simulate plugin execution."""
        payload = {
            "plugin": "webhook_handler",
            "action": "trigger",
            "data": {"test": "data", "timestamp": datetime.now().isoformat()}
        }
        response = self.client.post(
            "/api/v1/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)

    @task(8)
    def list_with_filtering(self):
        """List with various filters."""
        response = self.client.get(
            "/api/v1/plugins",
            params={
                "filter": "active",
                "sort": "name",
                "limit": 50,
                "offset": 0
            }
        )
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)


class StreamingUser(FastHttpUser):
    """Simulates users with streaming/long-lived connections."""

    wait_time = between(2, 5)  # Wait 2-5 seconds between requests
    task_weight = 10  # 10% of traffic

    @task(5)
    def stream_logs(self):
        """Stream logs from the system."""
        with self.client.stream(
            "GET",
            "/api/v1/logs/stream",
            params={"filter": "plugin", "follow": "true"},
            timeout=30
        ) as response:
            if response.status_code == 200:
                # Simulate reading from stream for a bit
                for i, line in enumerate(response.iter_lines()):
                    if i >= 10:  # Read 10 lines then stop
                        break
                load_test_stats.successful_requests += 1
            else:
                load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1

    @task(3)
    def subscribe_events(self):
        """Subscribe to real-time events."""
        response = self.client.get("/api/v1/events/subscribe", params={"timeout": 30})
        if response.status_code == 200:
            load_test_stats.successful_requests += 1
        else:
            load_test_stats.failed_requests += 1
        load_test_stats.total_requests += 1
        load_test_stats.response_times.append(response.elapsed.total_seconds() * 1000)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    load_test_stats.start_time = datetime.now()
    logger.info("Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    load_test_stats.end_time = datetime.now()
    logger.info("Load test stopped")

    # Log final stats
    stats = load_test_stats.to_dict()
    logger.info(f"\nLoad Test Results:\n{json.dumps(stats, indent=2)}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Called after each request."""
    if exception:
        logger.debug(f"Request failed: {name} - {exception}")
    else:
        logger.debug(f"Request succeeded: {name} - {response_time}ms")
