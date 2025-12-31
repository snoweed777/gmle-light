"""System management endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from gmle.app.api.internal.system_api import get_system_api
from gmle.app.api.rest.models import (
    ApiKeyStatusResponse,
    ServiceStatus,
    SystemStatusResponse,
)
from gmle.app.http.rate_limiter import get_rate_limiter
from gmle.app.infra.health_check import check_environment

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Get all services status."""
    try:
        system_api = get_system_api()
        # 非同期で実行してブロッキングを回避
        # これにより、APIサーバー自身のヘルスチェックが正常に動作する
        import asyncio
        result = await asyncio.to_thread(system_api.get_all_status)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        
        services = {}
        for service_name, service_data in result.get("services", {}).items():
            services[service_name] = ServiceStatus(**service_data)
        
        return SystemStatusResponse(services=services)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {e}",
        )


@router.get("/services/{service_name}/status", response_model=ServiceStatus)
async def get_service_status(service_name: str) -> ServiceStatus:
    """Get service status."""
    try:
        system_api = get_system_api()
        # 非同期で実行してブロッキングを回避
        import asyncio
        result = await asyncio.to_thread(system_api.get_service_status, service_name)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        
        return ServiceStatus(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {e}",
        )


@router.post("/services/{service_name}/start", response_model=ServiceStatus)
async def start_service(service_name: str) -> ServiceStatus:
    """Start service."""
    try:
        system_api = get_system_api()
        import asyncio
        result = await asyncio.to_thread(system_api.start_service, service_name)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        
        return ServiceStatus(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start service: {e}",
        )


@router.post("/services/{service_name}/stop", response_model=ServiceStatus)
async def stop_service(service_name: str) -> ServiceStatus:
    """Stop service."""
    try:
        system_api = get_system_api()
        # 非同期で実行してブロッキングを回避
        import asyncio
        result = await asyncio.to_thread(system_api.stop_service, service_name)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        
        return ServiceStatus(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop service: {e}",
        )


@router.post("/services/{service_name}/restart", response_model=ServiceStatus)
async def restart_service(service_name: str) -> ServiceStatus:
    """Restart service."""
    try:
        system_api = get_system_api()
        # 非同期で実行してブロッキングを回避
        import asyncio
        result = await asyncio.to_thread(system_api.restart_service, service_name)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )
        
        return ServiceStatus(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {e}",
        )


@router.get("/rate-limit")
async def get_rate_limit_status() -> Dict[str, Any]:
    """Get current rate limit status."""
    try:
        rate_limiter = get_rate_limiter()
        limiter_status = rate_limiter.get_status()
        return limiter_status  # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {e}",
        )


@router.get("/rate-limit/usage", response_model=Dict[str, Any])
async def get_rate_limit_usage() -> Dict[str, Any]:
    """Get API usage statistics."""
    try:
        import asyncio
        from gmle.app.http.usage_tracker import get_usage_tracker
        from gmle.app.config.getter import get_llm_config, get_rate_limit_config
        
        llm_config = get_llm_config()
        provider = llm_config.get("active_provider", "gemini")
        
        tracker = get_usage_tracker()
        usage = await asyncio.to_thread(tracker.get_usage, provider)
        
        # Get limits
        rate_limit_config = get_rate_limit_config()
        provider_limits = rate_limit_config.get("provider_daily_limits", {})
        daily_limit = provider_limits.get(provider, rate_limit_config.get("requests_per_day", 1400))
        
        # Calculate usage percentage
        daily_total = usage["daily"].get("total", 0)
        usage_percentage = (daily_total / daily_limit * 100) if daily_limit else 0
        
        return {
            "provider": provider,
            "usage": usage,
            "limits": {
                "daily": daily_limit,
                "hourly": rate_limit_config.get("requests_per_hour", 62),
                "minute": rate_limit_config.get("requests_per_minute", 10),
            },
            "usage_percentage": round(usage_percentage, 2),
            "status": "warning" if usage_percentage >= 90 else "ok" if usage_percentage < 80 else "caution",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage statistics: {e}",
        )


@router.get("/health")
async def get_health_check() -> Dict[str, Any]:
    """
    Get environment health check status.
    
    Checks:
    - Python dependencies
    - Required directories
    - File permissions
    - Configuration files
    """
    try:
        report = check_environment()
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run health check: {e}",
        )


@router.get("/api-keys/status", response_model=ApiKeyStatusResponse)
async def get_api_key_status() -> ApiKeyStatusResponse:
    """Check active LLM provider API key status."""
    try:
        import asyncio
        from gmle.app.config.getter import get_llm_config
        
        llm_config = get_llm_config()
        active_provider = llm_config.get("active_provider", "cohere")
        
        if active_provider == "cohere":
            from gmle.app.http.cohere_client import check_api_key_status as cohere_check
            status = await asyncio.to_thread(cohere_check)
        elif active_provider == "gemini":
            from gmle.app.http.gemini_client import check_api_key_status as gemini_check
            status = await asyncio.to_thread(gemini_check)
        elif active_provider == "groq":
            from gmle.app.http.groq_client import check_api_key_status as groq_check
            status = await asyncio.to_thread(groq_check)
        else:
            # For other providers, return not implemented
            status = {
                "valid": False,
                "error": f"API key check not implemented for provider: {active_provider}",
                "key_type": None,
                "has_quota": False,
            }
        
        return ApiKeyStatusResponse(**status)
    except Exception as e:
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check API key status: {e}",
        )

