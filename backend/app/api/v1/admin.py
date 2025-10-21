"""Admin endpoints for monitoring and management (TODO-9)"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.core.metrics import metrics_collector
from app.core.rate_limiter import get_rate_limiter
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/admin/costs")
async def get_costs() -> Dict[str, Any]:
    """
    Get OpenAI API cost summary (admin only)

    Returns cost tracking information:
    - Daily cost and usage percentage
    - Monthly cost and usage percentage
    - Cost limits

    Note: In production, this endpoint should be protected with authentication.
    """
    try:
        cost_summary = metrics_collector.get_cost_summary()
        metrics_summary = metrics_collector.get_summary()

        logger.info("Admin cost summary requested")

        return {
            "cost": cost_summary,
            "metrics": {
                "total_openai_calls": metrics_summary.get("total_openai_calls", 0),
                "openai_success_rate": metrics_summary.get("openai_success_rate", 0.0),
                "total_tokens_used": metrics_summary.get("total_tokens_used", 0),
                "openai_operations": metrics_summary.get("openai_operations", {})
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cost summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cost summary")


@router.get("/admin/rate-limits")
async def get_rate_limits() -> Dict[str, Any]:
    """
    Get rate limiter status (admin only)

    Returns rate limit configuration and current status:
    - Maximum requests per window
    - Window duration
    - Number of active clients being tracked

    Note: In production, this endpoint should be protected with authentication.
    """
    try:
        rate_limiter = get_rate_limiter()
        status = rate_limiter.get_status()

        logger.info("Admin rate limit status requested")

        return status
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit status")


@router.post("/admin/reset-rate-limit/{client_id}")
async def reset_rate_limit(client_id: str) -> Dict[str, str]:
    """
    Reset rate limit for specific client (admin only)

    Args:
        client_id: Client identifier (IP address) to reset

    Returns:
        Success message

    Note: In production, this endpoint should be protected with authentication.
    """
    try:
        rate_limiter = get_rate_limiter()
        rate_limiter.reset_client(client_id)

        logger.info(f"Admin reset rate limit for client: {client_id}")

        return {"message": f"Rate limit reset for client: {client_id}"}
    except Exception as e:
        logger.error(f"Failed to reset rate limit for {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset rate limit for {client_id}")


@router.get("/admin/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get full system metrics (admin only)

    Returns:
    - API call statistics
    - OpenAI API usage
    - Cost tracking
    - Error tracking
    - Rate limit status

    Note: In production, this endpoint should be protected with authentication.
    """
    try:
        metrics_summary = metrics_collector.get_summary()
        cost_summary = metrics_collector.get_cost_summary()
        rate_limiter = get_rate_limiter()
        rate_limit_status = rate_limiter.get_status()

        logger.info("Admin full metrics requested")

        return {
            "metrics": metrics_summary,
            "cost": cost_summary,
            "rate_limit": rate_limit_status
        }
    except Exception as e:
        logger.error(f"Failed to get full metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
