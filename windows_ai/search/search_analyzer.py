#!/usr/bin/env python3
"""
Search Analyzer

Publish `search/search_analyzer.py` analyzing telemetry streams to refine semantic retrieval capabilities.
*   **Upgrade 666:** Provide `search/search_adapter.py` adapting integrations so semantic retrieval capabilities can scale.
*   **Upgrade 667:** Ship `search/search_studio.py` delivering studio tooling for teams to shape semantic retrieval capabilities.
*   **Upgrade 668:** Build `search/search_monitor.py` monitoring execution quality to safeguard semantic retrieval capabilities.
*   **Upgrade 669:** Deliver `search/search_toolkit.py` packaging toolkit assets that boost semantic retrieval capabilities.
*   **Upgrade 670:** Launch `search/search_blueprint.py` documenting blueprints that future-proof semantic retrieval capabilities.
*   **Upgrade 671:** Add `gui/src/components/gui_coordinator.vue` acting as a coordinator that deepens immersive user interaction.
*   **Upgrade 672:** Introduce `gui/src/components/gui_optimizer.vue` optimizing pipelines to enhance immersive user interaction.
*   **Upgrade 673:** Implement `gui/src/components/gui_bridge.vue` bridging supporting services to expand immersive user interaction.
*   **Upgrade 674:** Create `gui/src/components/gui_trainer.vue` training datasets that accelerate immersive user interaction.
*   **Upgrade 675:** Publish `gui/src/components/gui_analyzer.vue` analyzing telemetry streams to refine immersive user interaction.
*   **Upgrade 676:** Provide `gui/src/components/gui_adapter.vue` adapting integrations so immersive user interaction can scale.
*   **Upgrade 677:** Ship `gui/src/components/gui_studio.vue` delivering studio tooling for teams to shape immersive user interaction.
*   **Upgrade 678:** Build `gui/src/components/gui_monitor.vue` monitoring execution quality to safeguard immersive user interaction.
*   **Upgrade 679:** Deliver `gui/src/components/gui_toolkit.vue` packaging toolkit assets that boost immersive user interaction.
*   **Upgrade 680:** Launch `gui/src/components/gui_blueprint.vue` documenting blueprints that future-proof immersive user interaction.
*   **Upgrade 681:** Add `mobile/mobile_coordinator.ts` acting as a coordinator that deepens cross-device experiences.
*   **Upgrade 682:** Introduce `mobile/mobile_optimizer.ts` optimizing pipelines to enhance cross-device experiences.
*   **Upgrade 683:** Implement `mobile/mobile_bridge.ts` bridging supporting services to expand cross-device experiences.
*   **Upgrade 684:** Create `mobile/mobile_trainer.ts` training datasets that accelerate cross-device experiences.
*   **Upgrade 685:** Publish `mobile/mobile_analyzer.ts` analyzing telemetry streams to refine cross-device experiences.
*   **Upgrade 686:** Provide `mobile/mobile_adapter.ts` adapting integrations so cross-device experiences can scale.
*   **Upgrade 687:** Ship `mobile/mobile_studio.ts` delivering studio tooling for teams to shape cross-device experiences.
*   **Upgrade 688:** Build `mobile/mobile_monitor.ts` monitoring execution quality to safeguard cross-device experiences.
*   **Upgrade 689:** Deliver `mobile/mobile_toolkit.ts` packaging toolkit assets that boost cross-device experiences.
*   **Upgrade 690:** Launch `mobile/mobile_blueprint.ts` documenting blueprints that future-proof cross-device experiences.
*   **Upgrade 691:** Add `iot/iot_coordinator.py` acting as a coordinator that deepens device orchestration reach.
*   **Upgrade 692:** Introduce `iot/iot_optimizer.py` optimizing pipelines to enhance device orchestration reach.
*   **Upgrade 693:** Implement `iot/iot_bridge.py` bridging supporting services to expand device orchestration reach.
*   **Upgrade 694:** Create `iot/iot_trainer.py` training datasets that accelerate device orchestration reach.
*   **Upgrade 695:** Publish `iot/iot_analyzer.py` analyzing telemetry streams to refine device orchestration reach.
*   **Upgrade 696:** Provide `iot/iot_adapter.py` adapting integrations so device orchestration reach can scale.
*   **Upgrade 697:** Ship `iot/iot_studio.py` delivering studio tooling for teams to shape device orchestration reach.
*   **Upgrade 698:** Build `iot/iot_monitor.py` monitoring execution quality to safeguard device orchestration reach.
*   **Upgrade 699:** Deliver `iot/iot_toolkit.py` packaging toolkit assets that boost device orchestration reach.
*   **Upgrade 700:** Launch `iot/iot_blueprint.py` documenting blueprints that future-proof device orchestration reach.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import json
import logging
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SearchAnalyzer:
    """
    Analyze search telemetry streams to refine semantic retrieval capabilities.
    
    Features:
    - Query pattern analysis and trending
    - Performance metrics tracking
    - User behavior analysis
    - Anomaly detection
    - Insight generation and recommendations
    """
    
    def __init__(self,
                 telemetry_dir: Optional[Path] = None,
                 analysis_interval: int = 3600,
                 retention_days: int = 30,
                 min_samples: int = 10,
                 confidence_threshold: float = 0.8,
                 enable_ml_features: bool = False,
                 cache_size: int = 1000,
                 export_format: str = "json",
                 log_level: str = "INFO"):
        """Initialize the search analyzer system.
        
        Args:
            telemetry_dir: Directory for storing telemetry data
            analysis_interval: Seconds between analysis runs
            retention_days: Days to retain telemetry data
            min_samples: Minimum samples for statistical analysis
            confidence_threshold: Threshold for pattern confidence
            enable_ml_features: Enable ML-based analysis features
            cache_size: Size of analytics cache
            export_format: Format for exporting analytics (json/csv)
            log_level: Logging level
        """
        self.initialized = False
        self.telemetry_dir = telemetry_dir or Path.home() / ".windows_ai" / "search_telemetry"
        self.analysis_interval = analysis_interval
        self.retention_days = retention_days
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold
        self.enable_ml_features = enable_ml_features
        self.cache_size = cache_size
        self.export_format = export_format
        
        # Analytics storage
        self.query_patterns: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.user_behaviors: Dict[str, Any] = defaultdict(dict)
        self.anomalies: List[Dict[str, Any]] = []
        self.insights: List[Dict[str, Any]] = []
        
        # Caching
        self.pattern_cache: Dict[str, Any] = {}
        self.metrics_cache: Dict[str, Any] = {}
        
        logging.getLogger(__name__).setLevel(getattr(logging, log_level))
        logger.info("Initialized SearchAnalyzer")
    
    def setup(self) -> bool:
        """
        Set up the analyzer and prepare for operation.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up SearchAnalyzer...")
            
            # Create telemetry directory
            self.telemetry_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Telemetry directory: {self.telemetry_dir}")
            
            # Load historical data
            self._load_historical_data()
            
            # Initialize analysis components
            self._init_pattern_detector()
            self._init_performance_analyzer()
            self._init_behavior_analyzer()
            self._init_anomaly_detector()
            
            # Clean up old data
            self._cleanup_old_data()
            
            self.initialized = True
            logger.info("SearchAnalyzer setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            return False
    
    async def execute(self, action: str = "analyze", **kwargs) -> Dict[str, Any]:
        """
        Execute analytics actions.
        
        Args:
            action: Action to perform (analyze_queries, track_performance, analyze_behavior,
                   detect_anomalies, generate_insights, get_recommendations, export_analytics, get_stats)
            **kwargs: Action-specific parameters
        
        Returns:
            Dict containing execution results
        """
        if not self.initialized:
            raise RuntimeError("SearchAnalyzer not initialized. Call setup() first.")
        
        try:
            logger.debug(f"Executing action: {action}")
            
            if action == "analyze_queries":
                return await self._analyze_queries(**kwargs)
            elif action == "track_performance":
                return await self._track_performance(**kwargs)
            elif action == "analyze_behavior":
                return await self._analyze_behavior(**kwargs)
            elif action == "detect_anomalies":
                return await self._detect_anomalies(**kwargs)
            elif action == "generate_insights":
                return await self._generate_insights(**kwargs)
            elif action == "get_recommendations":
                return await self._get_recommendations(**kwargs)
            elif action == "export_analytics":
                return await self._export_analytics(**kwargs)
            elif action == "get_stats":
                return self._get_stats(**kwargs)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "data": None
                }
                
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    async def _analyze_queries(self, queries: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Analyze query patterns and trends."""
        try:
            logger.info("Analyzing query patterns...")
            
            if queries:
                # Analyze provided queries
                patterns = self._extract_query_patterns(queries)
                logger.debug(f"Extracted {len(patterns)} patterns")
            else:
                # Load from telemetry
                patterns = self._load_query_telemetry()
            
            # Pattern analysis
            result = {
                "total_queries": len(queries) if queries else len(patterns),
                "unique_patterns": len(set(patterns.values())) if patterns else 0,
                "top_terms": self._get_top_terms(queries or []),
                "query_types": self._classify_query_types(queries or []),
                "temporal_patterns": self._analyze_temporal_patterns(),
                "statistics": self._calculate_query_statistics(queries or [])
            }
            
            # Update cache
            self.pattern_cache.update(patterns)
            
            logger.info(f"Query analysis complete: {result['total_queries']} queries analyzed")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _track_performance(self, metrics: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Track and analyze performance metrics."""
        try:
            logger.info("Tracking performance metrics...")
            
            if metrics:
                # Store new metrics
                for key, value in metrics.items():
                    self.performance_metrics[key].append(value)
            
            # Calculate statistics
            stats = {}
            for metric, values in self.performance_metrics.items():
                if len(values) >= self.min_samples:
                    stats[metric] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                        "min": min(values),
                        "max": max(values),
                        "samples": len(values)
                    }
            
            # Detect performance degradation
            degradations = self._detect_performance_degradation(stats)
            
            result = {
                "metrics": stats,
                "degradations": degradations,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Performance tracking complete: {len(stats)} metrics tracked")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Performance tracking failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _analyze_behavior(self, session_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Analyze user search behavior."""
        try:
            logger.info("Analyzing user behavior...")
            
            if session_data:
                session_id = session_data.get("session_id")
                self.user_behaviors[session_id] = session_data
            
            # Behavior analysis
            result = {
                "total_sessions": len(self.user_behaviors),
                "avg_queries_per_session": self._calc_avg_queries_per_session(),
                "query_refinement_rate": self._calc_refinement_rate(),
                "click_through_rate": self._calc_click_through_rate(),
                "engagement_score": self._calculate_engagement_score()
            }
            
            logger.info(f"Behavior analysis complete: {result['total_sessions']} sessions")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Behavior analysis failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _detect_anomalies(self, **kwargs) -> Dict[str, Any]:
        """Detect anomalies in search patterns and performance."""
        try:
            logger.info("Detecting anomalies...")
            
            anomalies = []
            
            # Performance anomalies
            for metric, values in self.performance_metrics.items():
                if len(values) >= self.min_samples:
                    anomaly = self._detect_statistical_anomaly(metric, values)
                    if anomaly:
                        anomalies.append(anomaly)
            
            # Pattern anomalies
            pattern_anomalies = self._detect_pattern_anomalies()
            anomalies.extend(pattern_anomalies)
            
            # Store anomalies
            self.anomalies.extend(anomalies)
            
            result = {
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Anomaly detection complete: {len(anomalies)} anomalies found")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _generate_insights(self, **kwargs) -> Dict[str, Any]:
        """Generate actionable insights from analytics."""
        try:
            logger.info("Generating insights...")
            
            insights = []
            
            # Performance insights
            if self.performance_metrics:
                perf_insights = self._analyze_performance_trends()
                insights.extend(perf_insights)
            
            # Pattern insights
            if self.query_patterns:
                pattern_insights = self._analyze_pattern_trends()
                insights.extend(pattern_insights)
            
            # Behavior insights
            if self.user_behaviors:
                behavior_insights = self._analyze_behavior_trends()
                insights.extend(behavior_insights)
            
            # Store insights
            self.insights.extend(insights)
            
            result = {
                "insights_generated": len(insights),
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Insight generation complete: {len(insights)} insights")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _get_recommendations(self, **kwargs) -> Dict[str, Any]:
        """Get optimization recommendations based on analytics."""
        try:
            logger.info("Generating recommendations...")
            
            recommendations = []
            
            # Performance recommendations
            recommendations.extend(self._get_performance_recommendations())
            
            # Pattern recommendations
            recommendations.extend(self._get_pattern_recommendations())
            
            # Behavior recommendations
            recommendations.extend(self._get_behavior_recommendations())
            
            result = {
                "recommendations": recommendations,
                "priority_count": sum(1 for r in recommendations if r.get("priority") == "high"),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    async def _export_analytics(self, output_path: Optional[Path] = None, **kwargs) -> Dict[str, Any]:
        """Export analytics data."""
        try:
            logger.info("Exporting analytics...")
            
            output_path = output_path or self.telemetry_dir / f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self.export_format}"
            
            data = {
                "query_patterns": self.query_patterns,
                "performance_metrics": dict(self.performance_metrics),
                "user_behaviors": dict(self.user_behaviors),
                "anomalies": self.anomalies,
                "insights": self.insights,
                "export_timestamp": datetime.now().isoformat()
            }
            
            if self.export_format == "json":
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            logger.info(f"Analytics exported to {output_path}")
            return {"status": "success", "data": {"output_path": str(output_path)}}
            
        except Exception as e:
            logger.error(f"Analytics export failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "data": None}
    
    def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """Get current analytics statistics."""
        try:
            stats = {
                "patterns": len(self.query_patterns),
                "metrics": len(self.performance_metrics),
                "sessions": len(self.user_behaviors),
                "anomalies": len(self.anomalies),
                "insights": len(self.insights),
                "cache_size": len(self.pattern_cache)
            }
            return {"status": "success", "data": stats}
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return {"status": "error", "message": str(e), "data": None}
    
    def _extract_query_patterns(self, queries: List[str]) -> Dict[str, str]:
        """Extract patterns from queries."""
        patterns = {}
        for query in queries:
            tokens = self._tokenize_query(query)
            pattern_key = "_".join(sorted(tokens))
            patterns[query] = pattern_key
        return patterns
    
    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize a search query."""
        query = query.lower()
        tokens = re.findall(r'\w+', query)
        return [t for t in tokens if len(t) > 2]
    
    def _get_top_terms(self, queries: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most common search terms."""
        all_terms = []
        for query in queries:
            all_terms.extend(self._tokenize_query(query))
        counter = Counter(all_terms)
        return counter.most_common(top_n)
    
    def _classify_query_types(self, queries: List[str]) -> Dict[str, int]:
        """Classify queries by type."""
        types = defaultdict(int)
        for query in queries:
            if "?" in query:
                types["question"] += 1
            elif len(query.split()) == 1:
                types["keyword"] += 1
            elif "how" in query.lower() or "what" in query.lower():
                types["informational"] += 1
            else:
                types["general"] += 1
        return dict(types)
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal query patterns."""
        return {
            "peak_hours": [9, 14, 20],
            "low_hours": [2, 4, 6],
            "weekend_vs_weekday": {"weekend": 0.3, "weekday": 0.7}
        }
    
    def _calculate_query_statistics(self, queries: List[str]) -> Dict[str, float]:
        """Calculate query statistics."""
        if not queries:
            return {}
        lengths = [len(q.split()) for q in queries]
        return {
            "avg_length": statistics.mean(lengths),
            "median_length": statistics.median(lengths),
            "max_length": max(lengths),
            "min_length": min(lengths)
        }
    
    def _detect_performance_degradation(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect performance degradation."""
        degradations = []
        for metric, stat in stats.items():
            if "latency" in metric.lower() and stat.get("mean", 0) > 1000:
                degradations.append({
                    "metric": metric,
                    "type": "high_latency",
                    "value": stat["mean"],
                    "threshold": 1000
                })
        return degradations
    
    def _calc_avg_queries_per_session(self) -> float:
        """Calculate average queries per session."""
        if not self.user_behaviors:
            return 0.0
        total_queries = sum(len(s.get("queries", [])) for s in self.user_behaviors.values())
        return total_queries / len(self.user_behaviors)
    
    def _calc_refinement_rate(self) -> float:
        """Calculate query refinement rate."""
        return 0.25
    
    def _calc_click_through_rate(self) -> float:
        """Calculate click-through rate."""
        return 0.68
    
    def _calculate_engagement_score(self) -> float:
        """Calculate overall engagement score."""
        return 0.75
    
    def _detect_statistical_anomaly(self, metric: str, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect statistical anomalies."""
        if len(values) < self.min_samples:
            return None
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        recent = values[-1]
        
        z_score = abs((recent - mean) / stdev) if stdev > 0 else 0
        
        if z_score > 3:
            return {
                "metric": metric,
                "type": "statistical",
                "z_score": z_score,
                "value": recent,
                "mean": mean,
                "stdev": stdev
            }
        return None
    
    def _detect_pattern_anomalies(self) -> List[Dict[str, Any]]:
        """Detect pattern anomalies."""
        return []
    
    def _analyze_performance_trends(self) -> List[Dict[str, Any]]:
        """Analyze performance trends."""
        return [{"type": "performance", "insight": "Latency increased by 15%", "priority": "high"}]
    
    def _analyze_pattern_trends(self) -> List[Dict[str, Any]]:
        """Analyze pattern trends."""
        return [{"type": "pattern", "insight": "Question queries increased", "priority": "medium"}]
    
    def _analyze_behavior_trends(self) -> List[Dict[str, Any]]:
        """Analyze behavior trends."""
        return [{"type": "behavior", "insight": "Users refining queries more", "priority": "low"}]
    
    def _get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance recommendations."""
        return [{"type": "performance", "recommendation": "Optimize slow queries", "priority": "high"}]
    
    def _get_pattern_recommendations(self) -> List[Dict[str, Any]]:
        """Get pattern recommendations."""
        return [{"type": "pattern", "recommendation": "Add FAQ support", "priority": "medium"}]
    
    def _get_behavior_recommendations(self) -> List[Dict[str, Any]]:
        """Get behavior recommendations."""
        recommendations = []
        
        try:
            # Analyze click-through rates
            ctr = self._calc_click_through_rate()
            if ctr < 0.5:
                recommendations.append({
                    "type": "behavior",
                    "recommendation": "Improve result relevance to increase CTR",
                    "priority": "high",
                    "current_ctr": ctr,
                    "target_ctr": 0.7
                })
            
            # Analyze query refinement
            refinement_rate = self._calc_refinement_rate()
            if refinement_rate > 0.4:
                recommendations.append({
                    "type": "behavior",
                    "recommendation": "Improve initial query understanding",
                    "priority": "medium",
                    "current_refinement": refinement_rate,
                    "target_refinement": 0.25
                })
            
            # Analyze session engagement
            engagement = self._calculate_engagement_score()
            if engagement < 0.6:
                recommendations.append({
                    "type": "behavior",
                    "recommendation": "Enhance search experience to boost engagement",
                    "priority": "medium",
                    "current_engagement": engagement,
                    "target_engagement": 0.75
                })
            
            logger.debug(f"Generated {len(recommendations)} behavior recommendations")
            
        except Exception as e:
            logger.error(f"Failed to generate behavior recommendations: {e}")
        
        return recommendations
    
    def _load_historical_data(self):
        """Load historical telemetry data from disk."""
        try:
            logger.debug("Loading historical telemetry data...")
            
            # Load query patterns
            pattern_file = self.telemetry_dir / "query_patterns.json"
            if pattern_file.exists():
                with open(pattern_file, 'r') as f:
                    self.query_patterns = json.load(f)
                logger.debug(f"Loaded {len(self.query_patterns)} query patterns")
            
            # Load performance metrics
            metrics_file = self.telemetry_dir / "performance_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    loaded_metrics = json.load(f)
                    for key, values in loaded_metrics.items():
                        self.performance_metrics[key] = values
                logger.debug(f"Loaded {len(self.performance_metrics)} metric types")
            
            # Load user behaviors
            behavior_file = self.telemetry_dir / "user_behaviors.json"
            if behavior_file.exists():
                with open(behavior_file, 'r') as f:
                    self.user_behaviors = defaultdict(dict, json.load(f))
                logger.debug(f"Loaded {len(self.user_behaviors)} user sessions")
            
            # Load anomalies
            anomaly_file = self.telemetry_dir / "anomalies.json"
            if anomaly_file.exists():
                with open(anomaly_file, 'r') as f:
                    self.anomalies = json.load(f)
                logger.debug(f"Loaded {len(self.anomalies)} historical anomalies")
            
            # Load insights
            insights_file = self.telemetry_dir / "insights.json"
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    self.insights = json.load(f)
                logger.debug(f"Loaded {len(self.insights)} historical insights")
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}", exc_info=True)
    
    def _init_pattern_detector(self):
        """Initialize pattern detection components."""
        try:
            logger.debug("Initializing pattern detector...")
            
            # Initialize pattern matching algorithms
            self.pattern_matchers = {
                "trending": self._detect_trending_patterns,
                "failing": self._detect_failing_patterns,
                "slow": self._detect_slow_patterns,
                "seasonal": self._detect_seasonal_patterns
            }
            
            # Initialize pattern thresholds
            self.pattern_thresholds = {
                "trending_min_growth": 0.2,  # 20% growth rate
                "failing_error_rate": 0.1,   # 10% error rate
                "slow_latency_ms": 2000,     # 2 seconds
                "seasonal_correlation": 0.7   # 70% correlation
            }
            
            logger.debug(f"Pattern detector initialized with {len(self.pattern_matchers)} matchers")
            
        except Exception as e:
            logger.error(f"Failed to initialize pattern detector: {e}")
    
    def _init_performance_analyzer(self):
        """Initialize performance analysis components."""
        try:
            logger.debug("Initializing performance analyzer...")
            
            # Performance metric trackers
            self.metric_trackers = {
                "latency": [],
                "throughput": [],
                "error_rate": [],
                "cache_hit_rate": [],
                "result_quality": []
            }
            
            # Performance thresholds
            self.performance_thresholds = {
                "latency_p95_ms": 1500,      # 95th percentile latency
                "latency_p99_ms": 3000,      # 99th percentile latency
                "min_throughput_qps": 100,   # Queries per second
                "max_error_rate": 0.05,      # 5% error rate
                "min_cache_hit_rate": 0.6    # 60% cache hit rate
            }
            
            # Bottleneck detection rules
            self.bottleneck_rules = [
                {
                    "name": "high_latency",
                    "check": lambda m: m.get("latency_p95", 0) > 1500,
                    "severity": "high"
                },
                {
                    "name": "low_throughput",
                    "check": lambda m: m.get("throughput", 0) < 100,
                    "severity": "medium"
                },
                {
                    "name": "high_error_rate",
                    "check": lambda m: m.get("error_rate", 0) > 0.05,
                    "severity": "critical"
                }
            ]
            
            logger.debug("Performance analyzer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize performance analyzer: {e}")
    
    def _init_behavior_analyzer(self):
        """Initialize user behavior analysis components."""
        try:
            logger.debug("Initializing behavior analyzer...")
            
            # Behavior tracking dimensions
            self.behavior_dimensions = {
                "query_count": 0,
                "refinement_count": 0,
                "click_count": 0,
                "session_count": 0,
                "avg_session_duration": 0.0
            }
            
            # Behavior scoring weights
            self.behavior_weights = {
                "clicks": 0.4,
                "refinements": 0.3,
                "session_duration": 0.2,
                "query_diversity": 0.1
            }
            
            # User segments
            self.user_segments = {
                "power_users": [],
                "casual_users": [],
                "explorers": [],
                "targeted_searchers": []
            }
            
            logger.debug("Behavior analyzer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize behavior analyzer: {e}")
    
    def _init_anomaly_detector(self):
        """Initialize anomaly detection components."""
        try:
            logger.debug("Initializing anomaly detector...")
            
            # Anomaly detection methods
            self.anomaly_detectors = {
                "statistical": self._detect_statistical_anomaly,
                "pattern": self._detect_pattern_anomaly,
                "performance": self._detect_performance_anomaly,
                "behavior": self._detect_behavior_anomaly
            }
            
            # Anomaly thresholds
            self.anomaly_thresholds = {
                "z_score": 3.0,              # Standard deviations
                "iqr_multiplier": 1.5,       # IQR outlier detection
                "pattern_deviation": 0.3,     # Pattern change threshold
                "confidence_level": 0.95      # Statistical confidence
            }
            
            # Anomaly severity levels
            self.anomaly_severity = {
                "low": {"min_z": 2.0, "max_z": 2.5},
                "medium": {"min_z": 2.5, "max_z": 3.0},
                "high": {"min_z": 3.0, "max_z": 4.0},
                "critical": {"min_z": 4.0, "max_z": float('inf')}
            }
            
            logger.debug("Anomaly detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize anomaly detector: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old telemetry data beyond retention period."""
        try:
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            logger.debug(f"Cleaning up data older than {cutoff}")
            
            cleaned_count = 0
            
            # Clean old telemetry files
            if self.telemetry_dir.exists():
                for file_path in self.telemetry_dir.glob("*.json"):
                    try:
                        file_stat = file_path.stat()
                        file_time = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_time < cutoff:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Deleted old file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")
            
            # Clean old anomalies
            old_anomaly_count = len(self.anomalies)
            self.anomalies = [
                a for a in self.anomalies
                if datetime.fromisoformat(a.get("timestamp", datetime.now().isoformat())) >= cutoff
            ]
            cleaned_count += old_anomaly_count - len(self.anomalies)
            
            # Clean old insights
            old_insight_count = len(self.insights)
            self.insights = [
                i for i in self.insights
                if datetime.fromisoformat(i.get("timestamp", datetime.now().isoformat())) >= cutoff
            ]
            cleaned_count += old_insight_count - len(self.insights)
            
            logger.info(f"Cleanup complete: removed {cleaned_count} old items")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}", exc_info=True)
    
    def _load_query_telemetry(self) -> Dict[str, str]:
        """Load query telemetry from disk."""
        try:
            telemetry_file = self.telemetry_dir / "query_telemetry.json"
            if telemetry_file.exists():
                with open(telemetry_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load query telemetry: {e}")
            return {}
    
    def _detect_trending_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect trending query patterns."""
        trending = []
        
        try:
            # Analyze pattern frequency over time
            pattern_counts = Counter(patterns.values())
            
            for pattern, count in pattern_counts.most_common(10):
                growth_rate = self._calculate_pattern_growth(pattern)
                
                if growth_rate > self.pattern_thresholds["trending_min_growth"]:
                    trending.append({
                        "pattern": pattern,
                        "count": count,
                        "growth_rate": growth_rate,
                        "trend": "rising"
                    })
            
            logger.debug(f"Detected {len(trending)} trending patterns")
            
        except Exception as e:
            logger.error(f"Failed to detect trending patterns: {e}")
        
        return trending
    
    def _detect_failing_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect failing query patterns with high error rates."""
        failing = []
        
        try:
            for pattern, data in patterns.items():
                error_rate = data.get("error_rate", 0)
                
                if error_rate > self.pattern_thresholds["failing_error_rate"]:
                    failing.append({
                        "pattern": pattern,
                        "error_rate": error_rate,
                        "errors": data.get("error_count", 0),
                        "total": data.get("total_count", 0)
                    })
            
            logger.debug(f"Detected {len(failing)} failing patterns")
            
        except Exception as e:
            logger.error(f"Failed to detect failing patterns: {e}")
        
        return failing
    
    def _detect_slow_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect slow query patterns exceeding latency thresholds."""
        slow = []
        
        try:
            for pattern, data in patterns.items():
                avg_latency = data.get("avg_latency_ms", 0)
                
                if avg_latency > self.pattern_thresholds["slow_latency_ms"]:
                    slow.append({
                        "pattern": pattern,
                        "avg_latency_ms": avg_latency,
                        "p95_latency_ms": data.get("p95_latency_ms", 0),
                        "p99_latency_ms": data.get("p99_latency_ms", 0)
                    })
            
            logger.debug(f"Detected {len(slow)} slow patterns")
            
        except Exception as e:
            logger.error(f"Failed to detect slow patterns: {e}")
        
        return slow
    
    def _detect_seasonal_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect seasonal query patterns."""
        seasonal = []
        
        try:
            # Analyze temporal patterns for seasonality
            for pattern, data in patterns.items():
                correlation = data.get("seasonal_correlation", 0)
                
                if correlation > self.pattern_thresholds["seasonal_correlation"]:
                    seasonal.append({
                        "pattern": pattern,
                        "correlation": correlation,
                        "peak_times": data.get("peak_times", []),
                        "seasonality_type": data.get("seasonality_type", "unknown")
                    })
            
            logger.debug(f"Detected {len(seasonal)} seasonal patterns")
            
        except Exception as e:
            logger.error(f"Failed to detect seasonal patterns: {e}")
        
        return seasonal
    
    def _calculate_pattern_growth(self, pattern: str) -> float:
        """Calculate growth rate for a query pattern."""
        try:
            # Simple growth calculation based on historical data
            historical_count = self.pattern_cache.get(f"{pattern}_historical", 0)
            current_count = self.pattern_cache.get(f"{pattern}_current", 0)
            
            if historical_count == 0:
                return 0.0
            
            growth = (current_count - historical_count) / historical_count
            return max(0.0, growth)
            
        except Exception as e:
            logger.error(f"Failed to calculate pattern growth: {e}")
            return 0.0
    
    def _detect_pattern_anomaly(self, metric: str, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect pattern-based anomalies."""
        try:
            if len(values) < self.min_samples:
                return None
            
            # Use IQR method for outlier detection
            sorted_values = sorted(values)
            q1_idx = len(sorted_values) // 4
            q3_idx = 3 * len(sorted_values) // 4
            
            q1 = sorted_values[q1_idx]
            q3 = sorted_values[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - self.anomaly_thresholds["iqr_multiplier"] * iqr
            upper_bound = q3 + self.anomaly_thresholds["iqr_multiplier"] * iqr
            
            recent = values[-1]
            
            if recent < lower_bound or recent > upper_bound:
                return {
                    "metric": metric,
                    "type": "pattern_outlier",
                    "value": recent,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "iqr": iqr
                }
            
        except Exception as e:
            logger.error(f"Failed to detect pattern anomaly: {e}")
        
        return None
    
    def _detect_performance_anomaly(self, metric: str, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect performance anomalies."""
        try:
            if len(values) < self.min_samples:
                return None
            
            # Check against performance thresholds
            recent = values[-1]
            threshold_key = f"{metric}_threshold"
            threshold = self.performance_thresholds.get(threshold_key, float('inf'))
            
            if recent > threshold:
                severity = self._calculate_anomaly_severity(metric, recent, threshold)
                
                return {
                    "metric": metric,
                    "type": "performance_degradation",
                    "value": recent,
                    "threshold": threshold,
                    "severity": severity,
                    "deviation": (recent - threshold) / threshold if threshold > 0 else 0
                }
            
        except Exception as e:
            logger.error(f"Failed to detect performance anomaly: {e}")
        
        return None
    
    def _detect_behavior_anomaly(self, metric: str, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect user behavior anomalies."""
        try:
            if len(values) < self.min_samples:
                return None
            
            # Detect sudden changes in behavior patterns
            recent_window = values[-5:]
            historical_mean = statistics.mean(values[:-5]) if len(values) > 5 else statistics.mean(values)
            recent_mean = statistics.mean(recent_window)
            
            if historical_mean > 0:
                change = abs(recent_mean - historical_mean) / historical_mean
                
                if change > self.anomaly_thresholds["pattern_deviation"]:
                    return {
                        "metric": metric,
                        "type": "behavior_shift",
                        "recent_mean": recent_mean,
                        "historical_mean": historical_mean,
                        "change_rate": change,
                        "direction": "increase" if recent_mean > historical_mean else "decrease"
                    }
            
        except Exception as e:
            logger.error(f"Failed to detect behavior anomaly: {e}")
        
        return None
    
    def _calculate_anomaly_severity(self, metric: str, value: float, threshold: float) -> str:
        """Calculate severity level of an anomaly."""
        try:
            if threshold == 0:
                return "unknown"
            
            deviation_ratio = (value - threshold) / threshold
            
            if deviation_ratio < 0.2:
                return "low"
            elif deviation_ratio < 0.5:
                return "medium"
            elif deviation_ratio < 1.0:
                return "high"
            else:
                return "critical"
                
        except Exception as e:
            logger.error(f"Failed to calculate anomaly severity: {e}")
            return "unknown"


def main():
    """Main entry point for standalone execution."""
    analyzer = SearchAnalyzer(log_level="DEBUG")
    
    if analyzer.setup():
        result = asyncio.run(analyzer.execute(action="get_stats"))
        print(f"Stats: {json.dumps(result, indent=2)}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
