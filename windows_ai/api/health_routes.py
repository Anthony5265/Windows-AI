"""
Health Check API Endpoints

Provides system health monitoring and diagnostics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from windows_ai.core.error_handling import HealthChecker, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health status response"""
    status: str  # healthy, unhealthy, degraded
    timestamp: str
    checks: Dict[str, Any]


class ComponentHealth(BaseModel):
    """Individual component health"""
    status: str  # healthy, unhealthy, warning, unknown
    message: str


@router.get("/", response_model=HealthStatus)
async def get_health_status():
    """
    Get overall system health status
    
    Returns health checks for all system components
    """
    try:
        health_checker = HealthChecker(logger)
        health = await health_checker.check_all()
        
        return HealthStatus(**health)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database", response_model=ComponentHealth)
async def check_database_health():
    """Check database health"""
    try:
        health_checker = HealthChecker(logger)
        result = await health_checker.check_database()
        
        return ComponentHealth(**result)
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unhealthy",
            message=f"Health check error: {str(e)}"
        )


@router.get("/disk", response_model=ComponentHealth)
async def check_disk_health():
    """Check disk space"""
    try:
        health_checker = HealthChecker(logger)
        result = await health_checker.check_disk_space()
        
        return ComponentHealth(**result)
    
    except Exception as e:
        logger.error(f"Disk health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unknown",
            message=f"Health check error: {str(e)}"
        )


@router.get("/memory", response_model=ComponentHealth)
async def check_memory_health():
    """Check memory usage"""
    try:
        health_checker = HealthChecker(logger)
        result = await health_checker.check_memory()
        
        return ComponentHealth(**result)
    
    except Exception as e:
        logger.error(f"Memory health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unknown",
            message=f"Health check error: {str(e)}"
        )


@router.get("/network", response_model=ComponentHealth)
async def check_network_health():
    """Check network connectivity"""
    try:
        health_checker = HealthChecker(logger)
        result = await health_checker.check_api_connectivity()
        
        return ComponentHealth(**result)
    
    except Exception as e:
        logger.error(f"Network health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unknown",
            message=f"Health check error: {str(e)}"
        )


@router.get("/plugins", response_model=ComponentHealth)
async def check_plugins_health():
    """Check plugin system health"""
    try:
        health_checker = HealthChecker(logger)
        result = await health_checker.check_plugins()
        
        return ComponentHealth(**result)
    
    except Exception as e:
        logger.error(f"Plugin health check failed: {e}", exc_info=True)
        return ComponentHealth(
            status="unknown",
            message=f"Health check error: {str(e)}"
        )


@router.get("/integrations")
async def check_integrations_health():
    """
    Check health of all integration managers.
    
    Returns initialization status for each integration manager,
    useful for verifying which AI providers and services are available.
    """
    try:
        import importlib
        import os
        
        manager_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "integrations")
        results = {}
        
        for fname in sorted(os.listdir(manager_dir)):
            if not fname.endswith('.py') or fname == '__init__.py':
                continue
            module_name = f"windows_ai.integrations.{fname[:-3]}"
            try:
                mod = importlib.import_module(module_name)
                for attr_name in dir(mod):
                    obj = getattr(mod, attr_name)
                    if isinstance(obj, type) and attr_name.endswith('Manager') and attr_name != 'Manager':
                        try:
                            instance = obj()
                            await instance.initialize()
                            results[attr_name] = {
                                "status": "healthy",
                                "initialized": getattr(instance, '_initialized', True),
                            }
                        except Exception as e:
                            results[attr_name] = {
                                "status": "unhealthy",
                                "error": str(e)[:200],
                            }
            except Exception as e:
                results[fname] = {
                    "status": "error",
                    "error": str(e)[:200],
                }
        
        healthy = sum(1 for v in results.values() if v["status"] == "healthy")
        total = len(results)
        
        return {
            "status": "healthy" if healthy == total else "degraded" if healthy > 0 else "unhealthy",
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "managers": results,
        }
    
    except Exception as e:
        logger.error(f"Integration health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(
    level: Optional[str] = None,
    limit: int = 100
):
    """
    Get recent log entries
    
    Args:
        level: Filter by log level (debug, info, warning, error, critical)
        limit: Maximum number of log entries to return
    """
    try:
        import json
        from pathlib import Path
        
        log_dir = Path.home() / ".windows_ai" / "logs"
        json_log_file = log_dir / "windows_ai.json"
        
        if not json_log_file.exists():
            return {"logs": [], "message": "No logs found"}
        
        # Read log file
        logs = []
        with open(json_log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    
                    # Filter by level if specified
                    if level and log_entry.get('level', '').lower() != level.lower():
                        continue
                    
                    logs.append(log_entry)
                    
                    if len(logs) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        # Get most recent logs
        logs = logs[-limit:]
        
        return {
            "logs": logs,
            "count": len(logs),
            "level_filter": level
        }
    
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/summary")
async def get_error_summary():
    """
    Get summary of recent errors
    
    Returns error counts by category and severity
    """
    try:
        import json
        from pathlib import Path
        from collections import defaultdict
        
        log_dir = Path.home() / ".windows_ai" / "logs"
        json_log_file = log_dir / "windows_ai.json"
        
        if not json_log_file.exists():
            return {
                "total_errors": 0,
                "by_level": {},
                "by_category": {},
                "recent_errors": []
            }
        
        errors_by_level = defaultdict(int)
        errors_by_category = defaultdict(int)
        recent_errors = []
        
        # Read log file
        with open(json_log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    
                    level = log_entry.get('level', '').upper()
                    if level in ['ERROR', 'CRITICAL']:
                        errors_by_level[level] += 1
                        
                        category = log_entry.get('context', {}).get('category', 'unknown')
                        errors_by_category[category] += 1
                        
                        recent_errors.append({
                            'timestamp': log_entry.get('timestamp'),
                            'level': level,
                            'message': log_entry.get('message'),
                            'category': category
                        })
                        
                except json.JSONDecodeError:
                    continue
        
        # Get most recent 20 errors
        recent_errors = recent_errors[-20:]
        
        return {
            "total_errors": sum(errors_by_level.values()),
            "by_level": dict(errors_by_level),
            "by_category": dict(errors_by_category),
            "recent_errors": recent_errors
        }
    
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
