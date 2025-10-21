"""Metrics API endpoints for monitoring and observability"""
from fastapi import APIRouter
from app.core.metrics import metrics_collector
from typing import Dict, Any, List

router = APIRouter()


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get metrics summary

    Returns aggregated metrics including:
    - API call statistics (count, response time, success rate)
    - OpenAI API usage (calls, tokens, success rate)
    - Error statistics (count, rate)
    """
    return metrics_collector.get_summary()


@router.get("/metrics/errors")
async def get_recent_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent errors

    Args:
        limit: Maximum number of errors to return (default: 10)

    Returns:
        List of recent error metrics
    """
    return metrics_collector.get_recent_errors(limit=limit)


@router.post("/metrics/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics

    Use this endpoint to clear metrics data (for memory management)
    """
    metrics_collector.reset()
    return {"status": "success", "message": "Metrics reset successfully"}


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint with metrics

    Returns:
        Health status based on metrics:
        - healthy: All systems operational
        - degraded: OpenAI success rate < 90%
        - unhealthy: Error rate > 5%
    """
    summary = metrics_collector.get_summary()
    status = "healthy"

    # Check error rate
    if summary.get("error_rate", 0) > 5:
        status = "unhealthy"
    # Check OpenAI success rate
    elif summary.get("openai_success_rate", 100) < 90:
        status = "degraded"

    return {
        "status": status,
        "metrics": summary
    }
