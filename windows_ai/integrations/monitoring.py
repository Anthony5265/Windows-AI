"""
Monitoring & Observability Manager - 15+ Services
Logging, metrics, tracing, error tracking
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
import time
from typing import Dict, List, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class MonitoringManager:
    """Unified monitoring across 15+ platforms"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== ERROR TRACKING ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def capture_exception(self, provider: str, exception: Exception, context: Dict = None):
        """Capture exception to error tracking service"""
        if provider == "sentry":
            return self._sentry_capture(exception, context)
        elif provider == "rollbar":
            return await self._rollbar_capture(exception, context)
        elif provider == "bugsnag":
            return self._bugsnag_capture(exception, context)
        elif provider == "raygun":
            return await self._raygun_capture(exception, context)

    def _sentry_capture(self, exception, context):
        try:
            import sentry_sdk
            # Don't re-initialize if already initialized
            # Sentry SDK handles global initialization
            with sentry_sdk.push_scope() as scope:
                for key, value in (context or {}).items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(exception)
        except ImportError:
            logger.warning("Sentry SDK not available - exception not captured")
        except Exception as e:
            logger.error(f"Failed to capture exception to Sentry: {e}")

    async def _rollbar_capture(self, exception, context):
        import rollbar
        rollbar.init(os.environ.get("ROLLBAR_TOKEN"))
        rollbar.report_exc_info(extra_data=context)

    def _bugsnag_capture(self, exception, context):
        import bugsnag
        bugsnag.configure(api_key=os.environ.get("BUGSNAG_API_KEY"))
        bugsnag.notify(exception, meta_data=context)

    async def _raygun_capture(self, exception, context):
        from raygun4py import raygunprovider
        client = raygunprovider.RaygunSender(os.environ.get("RAYGUN_API_KEY"))
        client.send_exception(exception, tags=list(context.keys()) if context else [])

    # ==================== METRICS ====================

    async def send_metric(self, provider: str, name: str, value: float, tags: Dict = None):
        """Send metric to monitoring service"""
        if provider == "datadog":
            return self._datadog_metric(name, value, tags)
        elif provider == "prometheus":
            return self._prometheus_metric(name, value, tags)
        elif provider == "newrelic":
            return self._newrelic_metric(name, value, tags)
        elif provider == "cloudwatch":
            return await self._cloudwatch_metric(name, value, tags)

    def _datadog_metric(self, name, value, tags):
        from datadog import initialize, statsd
        initialize(api_key=os.environ.get("DD_API_KEY"), app_key=os.environ.get("DD_APP_KEY"))
        tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
        statsd.gauge(name, value, tags=tag_list)

    def _prometheus_metric(self, name, value, tags):
        from prometheus_client import Gauge
        g = Gauge(name, name, list((tags or {}).keys()))
        g.labels(**tags or {}).set(value)

    def _newrelic_metric(self, name, value, tags):
        import newrelic.agent
        newrelic.agent.record_custom_metric(name, value, application=newrelic.agent.application())

    async def _cloudwatch_metric(self, name, value, tags):
        import boto3
        cloudwatch = boto3.client("cloudwatch")
        dimensions = [{"Name": k, "Value": str(v)} for k, v in (tags or {}).items()]
        cloudwatch.put_metric_data(
            Namespace="WindowsAI",
            MetricData=[{"MetricName": name, "Value": value, "Dimensions": dimensions}]
        )

    # ==================== LOGGING ====================

    async def send_log(self, provider: str, message: str, level: str = "info", metadata: Dict = None):
        """Send log to logging service"""
        if provider == "logtail":
            return await self._logtail_log(message, level, metadata)
        elif provider == "papertrail":
            return await self._papertrail_log(message, level, metadata)
        elif provider == "logflare":
            return await self._logflare_log(message, level, metadata)
        elif provider == "axiom":
            return await self._axiom_log(message, level, metadata)

    async def _logtail_log(self, message, level, metadata):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://in.logtail.com",
                headers={"Authorization": f"Bearer {os.environ.get('LOGTAIL_TOKEN')}"},
                json={"message": message, "level": level, **(metadata or {})}
            ) as response:
                return response.status == 202

    async def _papertrail_log(self, message, level, metadata):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                os.environ.get("PAPERTRAIL_URL"),
                json={"message": message, "level": level, **(metadata or {})}
            ) as response:
                return response.status == 200

    async def _logflare_log(self, message, level, metadata):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.logflare.app/logs/json?source={os.environ.get('LOGFLARE_SOURCE')}",
                headers={"X-API-KEY": os.environ.get("LOGFLARE_API_KEY")},
                json={"message": message, "metadata": {"level": level, **(metadata or {})}}
            ) as response:
                return response.status == 200

    async def _axiom_log(self, message, level, metadata):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.axiom.co/v1/datasets/{os.environ.get('AXIOM_DATASET')}/ingest",
                headers={"Authorization": f"Bearer {os.environ.get('AXIOM_TOKEN')}"},
                json=[{"message": message, "level": level, **(metadata or {}), "_time": time.time()}]
            ) as response:
                return response.status == 200

    # ==================== TRACING ====================

    def start_trace(self, provider: str, operation: str, tags: Dict = None):
        """Start a trace span"""
        if provider == "jaeger":
            return self._jaeger_trace(operation, tags)
        elif provider == "zipkin":
            return self._zipkin_trace(operation, tags)
        elif provider == "opentelemetry":
            return self._otel_trace(operation, tags)

    def _otel_trace(self, operation, tags):
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(operation)
        for k, v in (tags or {}).items():
            span.set_attribute(k, v)
        return span

    def _jaeger_trace(self, operation, tags):
        from jaeger_client import Config
        config = Config(config={"sampler": {"type": "const", "param": 1}}, service_name="windowsai")
        tracer = config.initialize_tracer()
        span = tracer.start_span(operation)
        for k, v in (tags or {}).items():
            span.set_tag(k, v)
        return span

    def _zipkin_trace(self, operation, tags):
        from py_zipkin.zipkin import zipkin_span
        return zipkin_span(service_name="windowsai", span_name=operation)

    # ==================== APM ====================

    async def apm_transaction(self, provider: str, name: str, transaction_type: str = "request"):
        """Start APM transaction"""
        if provider == "elastic_apm":
            import elasticapm
            client = elasticapm.Client(service_name="windowsai")
            return client.begin_transaction(transaction_type)
        elif provider == "newrelic":
            import newrelic.agent
            return newrelic.agent.current_transaction()

    # ==================== UPTIME MONITORING ====================

    async def create_uptime_check(self, provider: str, url: str, name: str, interval: int = 60) -> Dict:
        """Create uptime monitor"""
        if provider == "uptime_robot":
            return await self._uptimerobot_create(url, name, interval)
        elif provider == "pingdom":
            return await self._pingdom_create(url, name, interval)
        elif provider == "betterstack":
            return await self._betterstack_create(url, name, interval)

    async def _uptimerobot_create(self, url, name, interval):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.uptimerobot.com/v2/newMonitor",
                json={
                    "api_key": os.environ.get("UPTIMEROBOT_API_KEY"),
                    "friendly_name": name,
                    "url": url,
                    "type": 1,
                    "interval": interval
                }
            ) as response:
                return await response.json()

    async def _betterstack_create(self, url, name, interval):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://uptime.betterstack.com/api/v2/monitors",
                headers={"Authorization": f"Bearer {os.environ.get('BETTERSTACK_API_KEY')}"},
                json={"url": url, "name": name, "check_frequency": interval}
            ) as response:
                return await response.json()

    def list_providers(self) -> Dict[str, List[str]]:
        return {
            "error_tracking": ["sentry", "rollbar", "bugsnag", "raygun", "honeybadger"],
            "metrics": ["datadog", "prometheus", "newrelic", "cloudwatch", "grafana"],
            "logging": ["logtail", "papertrail", "logflare", "axiom", "elastic"],
            "tracing": ["jaeger", "zipkin", "opentelemetry", "datadog"],
            "uptime": ["uptime_robot", "pingdom", "betterstack", "statuscake"]
        }
