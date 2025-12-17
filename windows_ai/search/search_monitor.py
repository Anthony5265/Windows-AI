#!/usr/bin/env python3
"""
Search Monitor

Build `search/search_monitor.py` monitoring execution quality to safeguard semantic retrieval capabilities.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SearchMonitor:
    """
    Monitor search quality and performance metrics to safeguard semantic retrieval capabilities.
    
    This class provides real-time tracking of search operations including quality metrics
    (precision, recall, F1 score), performance monitoring (latency, throughput), anomaly
    detection, and automated alerting capabilities.
    
    Features:
    - Real-time metrics tracking with sliding windows
    - Quality metrics calculation (precision, recall, F1)
    - Performance monitoring (latency, throughput, error rates)
    - Anomaly detection using statistical analysis
    - Configurable alerting system
    - Dashboard data export in JSON/CSV formats
    - Historical trend analysis
    
    Example:
        monitor = SearchMonitor(
            metrics_dir=Path("metrics"),
            alert_threshold=0.8,
            window_size=1000
        )
        await monitor.setup()
        
        # Track a query
        await monitor.execute(
            action="track_query",
            query="example search",
            results=search_results,
            latency_ms=150,
            relevance_scores=[0.9, 0.8, 0.7]
        )
        
        # Get metrics
        metrics = await monitor.execute(action="get_metrics")
    """
    
    def __init__(
        self,
        metrics_dir: Optional[Path] = None,
        alert_threshold: float = 0.8,
        window_size: int = 1000,
        anomaly_std_threshold: float = 3.0
    ):
        """
        Initialize the search monitor system.
        
        Args:
            metrics_dir: Directory to store metrics data (default: ~/.windows_ai/search_metrics)
            alert_threshold: Quality threshold below which to trigger alerts (0.0-1.0)
            window_size: Number of recent queries to keep in sliding window
            anomaly_std_threshold: Number of standard deviations for anomaly detection
        """
        self.initialized = False
        self.metrics_dir = metrics_dir or Path.home() / ".windows_ai" / "search_metrics"
        self.alert_threshold = alert_threshold
        self.window_size = window_size
        self.anomaly_std_threshold = anomaly_std_threshold
        
        # Metrics storage
        self.query_history: deque = deque(maxlen=window_size)
        self.latency_history: deque = deque(maxlen=window_size)
        self.quality_history: deque = deque(maxlen=window_size)
        self.error_count = 0
        self.total_queries = 0
        
        # Real-time metrics
        self.current_metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.start_time = time.time()
        
        logger.info(f"Initialized SearchMonitor with window_size={window_size}")
    
    async def setup(self) -> bool:
        """
        Set up the monitoring system and prepare for operation.
        
        Creates necessary directories, initializes metric tracking,
        and validates configuration.
        
        Returns:
            True if setup successful, False otherwise
        """
        if self.initialized:
            logger.warning("SearchMonitor already initialized")
            return True
        
        try:
            logger.info("Setting up SearchMonitor...")
            
            # Create metrics directory
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created metrics directory: {self.metrics_dir}")
            
            # Initialize metrics file
            metrics_file = self.metrics_dir / "metrics.json"
            if not metrics_file.exists():
                initial_metrics = {
                    "created_at": datetime.now().isoformat(),
                    "total_queries": 0,
                    "total_errors": 0,
                    "alerts": []
                }
                await self._write_json(metrics_file, initial_metrics)
            
            # Load existing metrics if available
            await self._load_historical_metrics()
            
            self.initialized = True
            logger.info("SearchMonitor setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SearchMonitor setup failed: {e}", exc_info=True)
            return False
    
    async def execute(self, action: str = "track_query", **kwargs) -> Dict[str, Any]:
        """
        Execute monitoring operations.
        
        Args:
            action: Operation to perform - "track_query", "get_metrics", 
                   "export_dashboard", "check_anomalies", "get_alerts"
            **kwargs: Action-specific parameters
            
        Returns:
            Dict containing execution results with status, data, and metadata
            
        Raises:
            RuntimeError: If monitor not initialized
        """
        if not self.initialized:
            raise RuntimeError("SearchMonitor not initialized. Call setup() first.")
        
        try:
            logger.debug(f"Executing SearchMonitor action: {action}")
            
            if action == "track_query":
                return await self._track_query(**kwargs)
            elif action == "get_metrics":
                return await self._calculate_metrics()
            elif action == "export_dashboard":
                format_type = kwargs.get("format", "json")
                return await self._export_metrics(format_type)
            elif action == "check_anomalies":
                return await self._detect_anomalies()
            elif action == "get_alerts":
                return await self._get_alerts()
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"SearchMonitor execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    async def _track_query(
        self,
        query: str,
        results: List[Dict[str, Any]],
        latency_ms: float,
        relevance_scores: Optional[List[float]] = None,
        expected_results: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Track a search query and update metrics.
        
        Args:
            query: The search query string
            results: List of search results
            latency_ms: Query latency in milliseconds
            relevance_scores: Optional relevance scores for results
            expected_results: Optional expected result IDs for quality calculation
            
        Returns:
            Dict with tracking status and updated metrics
        """
        try:
            self.total_queries += 1
            
            # Track query metadata
            query_data = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "result_count": len(results),
                "latency_ms": latency_ms,
                "relevance_scores": relevance_scores or []
            }
            
            # Update history
            self.query_history.append(query_data)
            self.latency_history.append(latency_ms)
            
            # Calculate quality metrics if expected results provided
            quality_score = 0.0
            if expected_results and results:
                quality_metrics = self._calculate_quality_metrics(
                    results, expected_results, relevance_scores
                )
                quality_score = quality_metrics.get("f1_score", 0.0)
                query_data["quality_metrics"] = quality_metrics
            
            self.quality_history.append(quality_score)
            
            # Check for quality degradation
            if quality_score > 0 and quality_score < self.alert_threshold:
                await self._create_alert(
                    "quality_degradation",
                    f"Query quality score {quality_score:.2f} below threshold {self.alert_threshold}",
                    {"query": query, "score": quality_score}
                )
            
            # Check for latency spikes
            if len(self.latency_history) >= 10:
                avg_latency = statistics.mean(list(self.latency_history)[-10:])
                if latency_ms > avg_latency * 2:
                    await self._create_alert(
                        "latency_spike",
                        f"Query latency {latency_ms}ms is 2x average {avg_latency:.0f}ms",
                        {"query": query, "latency_ms": latency_ms}
                    )
            
            logger.debug(f"Tracked query: {query[:50]}... (latency: {latency_ms}ms)")
            
            return {
                "status": "success",
                "message": "Query tracked successfully",
                "data": {
                    "total_queries": self.total_queries,
                    "latency_ms": latency_ms,
                    "quality_score": quality_score
                }
            }
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to track query: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    def _calculate_quality_metrics(
        self,
        results: List[Dict[str, Any]],
        expected_results: List[str],
        relevance_scores: Optional[List[float]] = None
    ) -> Dict[str, float]:
        """
        Calculate precision, recall, and F1 score for search results.
        
        Args:
            results: Retrieved search results
            expected_results: Expected/ground truth result IDs
            relevance_scores: Optional relevance scores
            
        Returns:
            Dict with precision, recall, f1_score, and additional metrics
        """
        try:
            # Extract result IDs
            result_ids = [r.get("id", str(i)) for i, r in enumerate(results)]
            
            # Calculate true positives, false positives, false negatives
            true_positives = len(set(result_ids) & set(expected_results))
            false_positives = len(set(result_ids) - set(expected_results))
            false_negatives = len(set(expected_results) - set(result_ids))
            
            # Calculate precision and recall
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            
            # Calculate F1 score
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            # Calculate mean relevance if available
            mean_relevance = statistics.mean(relevance_scores) if relevance_scores else 0.0
            
            metrics = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "mean_relevance": mean_relevance
            }
            
            logger.debug(f"Quality metrics: P={precision:.3f}, R={recall:.3f}, F1={f1_score:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "mean_relevance": 0.0
            }
    
    async def _calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate current performance and quality metrics.
        
        Returns:
            Dict containing comprehensive metrics including latency stats,
            quality scores, throughput, and error rates
        """
        try:
            uptime_seconds = time.time() - self.start_time
            
            # Calculate latency statistics
            latency_stats = {}
            if self.latency_history:
                latencies = list(self.latency_history)
                latency_stats = {
                    "mean_ms": statistics.mean(latencies),
                    "median_ms": statistics.median(latencies),
                    "min_ms": min(latencies),
                    "max_ms": max(latencies),
                    "p95_ms": self._calculate_percentile(latencies, 95),
                    "p99_ms": self._calculate_percentile(latencies, 99)
                }
            
            # Calculate quality statistics
            quality_stats = {}
            if self.quality_history:
                quality_scores = [q for q in self.quality_history if q > 0]
                if quality_scores:
                    quality_stats = {
                        "mean_score": statistics.mean(quality_scores),
                        "median_score": statistics.median(quality_scores),
                        "min_score": min(quality_scores),
                        "max_score": max(quality_scores)
                    }
            
            # Calculate throughput
            queries_per_second = self.total_queries / uptime_seconds if uptime_seconds > 0 else 0.0
            
            # Calculate error rate
            error_rate = self.error_count / self.total_queries if self.total_queries > 0 else 0.0
            
            metrics = {
                "status": "success",
                "data": {
                    "uptime_seconds": uptime_seconds,
                    "total_queries": self.total_queries,
                    "total_errors": self.error_count,
                    "error_rate": error_rate,
                    "queries_per_second": queries_per_second,
                    "latency": latency_stats,
                    "quality": quality_stats,
                    "active_alerts": len(self.alerts),
                    "window_size": len(self.query_history),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self.current_metrics = metrics["data"]
            logger.info(f"Calculated metrics: {self.total_queries} queries, {queries_per_second:.2f} qps")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    async def _detect_anomalies(self) -> Dict[str, Any]:
        """
        Detect anomalies in search performance using statistical analysis.
        
        Uses standard deviation thresholds to identify outliers in latency
        and quality metrics.
        
        Returns:
            Dict with detected anomalies and their severity
        """
        try:
            anomalies = []
            
            # Check latency anomalies
            if len(self.latency_history) >= 30:
                latencies = list(self.latency_history)
                mean_latency = statistics.mean(latencies)
                std_latency = statistics.stdev(latencies)
                
                for i, latency in enumerate(latencies[-10:]):  # Check last 10 queries
                    z_score = (latency - mean_latency) / std_latency if std_latency > 0 else 0
                    if abs(z_score) > self.anomaly_std_threshold:
                        anomalies.append({
                            "type": "latency_anomaly",
                            "severity": "high" if abs(z_score) > 4 else "medium",
                            "value": latency,
                            "z_score": z_score,
                            "mean": mean_latency,
                            "std": std_latency
                        })
            
            # Check quality anomalies
            quality_scores = [q for q in self.quality_history if q > 0]
            if len(quality_scores) >= 30:
                mean_quality = statistics.mean(quality_scores)
                std_quality = statistics.stdev(quality_scores)
                
                for quality in quality_scores[-10:]:
                    z_score = (quality - mean_quality) / std_quality if std_quality > 0 else 0
                    if z_score < -self.anomaly_std_threshold:  # Below mean
                        anomalies.append({
                            "type": "quality_anomaly",
                            "severity": "high" if z_score < -4 else "medium",
                            "value": quality,
                            "z_score": z_score,
                            "mean": mean_quality,
                            "std": std_quality
                        })
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            
            return {
                "status": "success",
                "data": {
                    "anomaly_count": len(anomalies),
                    "anomalies": anomalies,
                    "threshold": self.anomaly_std_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    async def _create_alert(self, alert_type: str, message: str, context: Dict[str, Any]) -> None:
        """
        Create and store an alert for monitoring issues.
        
        Args:
            alert_type: Type of alert (quality_degradation, latency_spike, etc.)
            message: Human-readable alert message
            context: Additional context data
        """
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": alert_type,
                "message": message,
                "context": context,
                "acknowledged": False
            }
            
            self.alerts.append(alert)
            logger.warning(f"Alert created: {alert_type} - {message}")
            
            # Persist alert to disk
            alerts_file = self.metrics_dir / "alerts.json"
            await self._append_json(alerts_file, alert)
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _get_alerts(self) -> Dict[str, Any]:
        """
        Retrieve current active alerts.
        
        Returns:
            Dict containing all active alerts
        """
        return {
            "status": "success",
            "data": {
                "total_alerts": len(self.alerts),
                "alerts": self.alerts
            }
        }
    
    async def _export_metrics(self, format_type: str = "json") -> Dict[str, Any]:
        """
        Export metrics for dashboard visualization.
        
        Args:
            format_type: Export format - "json" or "csv"
            
        Returns:
            Dict with export status and file path
        """
        try:
            # Calculate comprehensive metrics
            metrics_data = await self._calculate_metrics()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "json":
                export_file = self.metrics_dir / f"dashboard_export_{timestamp}.json"
                await self._write_json(export_file, metrics_data)
            elif format_type == "csv":
                export_file = self.metrics_dir / f"dashboard_export_{timestamp}.csv"
                await self._write_csv(export_file, metrics_data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Exported metrics to: {export_file}")
            
            return {
                "status": "success",
                "message": f"Metrics exported to {format_type.upper()}",
                "data": {
                    "export_file": str(export_file),
                    "format": format_type,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value from data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def _write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write data to JSON file asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_text(json.dumps(data, indent=2))
        )
    
    async def _append_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Append data to JSON array file."""
        try:
            existing_data = []
            if file_path.exists():
                content = await asyncio.get_event_loop().run_in_executor(
                    None, file_path.read_text
                )
                existing_data = json.loads(content) if content else []
            
            existing_data.append(data)
            await self._write_json(file_path, existing_data)
            
        except Exception as e:
            logger.error(f"Failed to append to JSON: {e}")
    
    async def _write_csv(self, file_path: Path, metrics_data: Dict[str, Any]) -> None:
        """Write metrics to CSV file."""
        try:
            import csv
            
            data = metrics_data.get("data", {})
            
            rows = [
                ["Metric", "Value"],
                ["Uptime (seconds)", data.get("uptime_seconds", 0)],
                ["Total Queries", data.get("total_queries", 0)],
                ["Total Errors", data.get("total_errors", 0)],
                ["Error Rate", data.get("error_rate", 0)],
                ["Queries/Second", data.get("queries_per_second", 0)],
            ]
            
            # Add latency stats
            latency = data.get("latency", {})
            for key, value in latency.items():
                rows.append([f"Latency {key}", value])
            
            # Add quality stats
            quality = data.get("quality", {})
            for key, value in quality.items():
                rows.append([f"Quality {key}", value])
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._write_csv_sync(file_path, rows)
            )
            
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")
    
    def _write_csv_sync(self, file_path: Path, rows: List[List]) -> None:
        """Synchronous CSV write helper."""
        import csv
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    async def _load_historical_metrics(self) -> None:
        """Load historical metrics from disk if available."""
        try:
            metrics_file = self.metrics_dir / "metrics.json"
            if metrics_file.exists():
                content = await asyncio.get_event_loop().run_in_executor(
                    None, metrics_file.read_text
                )
                historical = json.loads(content)
                self.total_queries = historical.get("total_queries", 0)
                self.error_count = historical.get("total_errors", 0)
                logger.debug(f"Loaded historical metrics: {self.total_queries} queries")
        except Exception as e:
            logger.warning(f"Could not load historical metrics: {e}")


async def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = SearchMonitor()
    
    if await monitor.setup():
        # Example: Track some queries
        for i in range(5):
            result = await monitor.execute(
                action="track_query",
                query=f"example query {i}",
                results=[{"id": f"doc_{j}", "score": 0.9 - j*0.1} for j in range(3)],
                latency_ms=100 + i * 10,
                relevance_scores=[0.9, 0.8, 0.7]
            )
            print(f"Query {i}: {result['status']}")
        
        # Get metrics
        metrics = await monitor.execute(action="get_metrics")
        print(f"\nMetrics: {json.dumps(metrics, indent=2)}")
        
        # Check anomalies
        anomalies = await monitor.execute(action="check_anomalies")
        print(f"\nAnomalies: {anomalies['data']['anomaly_count']}")
        
        # Export dashboard
        export = await monitor.execute(action="export_dashboard", format="json")
        print(f"\nExported to: {export['data']['export_file']}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    asyncio.run(main())
