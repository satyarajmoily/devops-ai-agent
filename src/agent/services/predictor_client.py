"""HTTP client for communicating with the Market Predictor service."""

import asyncio
import time
from typing import Dict, Optional

import httpx
from pydantic import BaseModel

from agent.config.settings import get_settings


class PredictorHealthResponse(BaseModel):
    """Market Predictor health response model."""
    status: str
    timestamp: str
    service: str
    version: str


class PredictorStatusResponse(BaseModel):
    """Market Predictor detailed status response model."""
    status: str
    timestamp: str
    service: str
    version: str
    uptime_seconds: float
    components: Dict[str, str]
    metadata: Optional[Dict[str, str]] = None


class PredictorClient:
    """HTTP client for Market Predictor service communication."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """Initialize the predictor client.
        
        Args:
            base_url: Base URL for the Market Predictor service
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self.base_url = base_url or settings.market_predictor_url
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
            
        Raises:
            httpx.RequestError: For network/connection errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = await self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise httpx.RequestError(f"Request timeout to {url}") from e
        except httpx.ConnectError as e:
            raise httpx.RequestError(f"Connection error to {url}") from e
    
    async def health_check(self) -> PredictorHealthResponse:
        """Perform health check on Market Predictor service.
        
        Returns:
            Health status response
            
        Raises:
            httpx.RequestError: For network/connection errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        response = await self._make_request("GET", "/health")
        return PredictorHealthResponse(**response.json())
    
    async def get_status(self) -> PredictorStatusResponse:
        """Get detailed status from Market Predictor service.
        
        Returns:
            Detailed status response
            
        Raises:
            httpx.RequestError: For network/connection errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        response = await self._make_request("GET", "/status")
        return PredictorStatusResponse(**response.json())
    
    async def get_service_info(self) -> Dict:
        """Get basic service information from root endpoint.
        
        Returns:
            Service information dictionary
            
        Raises:
            httpx.RequestError: For network/connection errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        response = await self._make_request("GET", "/")
        return response.json()
    
    async def check_connectivity(self) -> tuple[bool, Optional[str], Optional[float]]:
        """Check connectivity to Market Predictor service.
        
        Returns:
            Tuple of (is_connected, error_message, response_time_ms)
        """
        start_time = time.time()
        
        try:
            await self.health_check()
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return True, None, response_time
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, str(e), response_time


# Convenience function for quick health checks
async def quick_health_check(base_url: Optional[str] = None, timeout: int = 5) -> tuple[bool, Optional[str]]:
    """Perform a quick health check on the Market Predictor service.
    
    Args:
        base_url: Base URL for the service
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        async with PredictorClient(base_url, timeout) as client:
            await client.health_check()
            return True, None
    except Exception as e:
        return False, str(e)