"""HTTP client for GoHighLevel API."""

from __future__ import annotations

import time
from typing import Any, ClassVar, Literal, Optional

import httpx
from pydantic import BaseModel

from .config import config_manager


class RateLimitInfo(BaseModel):
    """Rate limit information from API response headers."""

    limit: int = 100
    remaining: int = 100
    reset: Optional[float] = None
    interval_ms: int = 10000

    RATE_LIMIT_HEADERS: ClassVar[tuple[str, ...]] = (
        "x-ratelimit-remaining",
        "x-ratelimit-max",
        "x-ratelimit-limit",
    )

    @classmethod
    def has_rate_limit_headers(cls, headers: httpx.Headers) -> bool:
        """True if response has rate limit headers (GHL doesn't send them on all endpoints)."""
        for name in cls.RATE_LIMIT_HEADERS:
            if headers.get(name) is not None:
                return True
        return False

    @classmethod
    def from_headers(cls, headers: httpx.Headers) -> "RateLimitInfo":
        """Parse rate limit info from GoHighLevel API response headers.

        GHL uses: X-RateLimit-Max, X-RateLimit-Remaining, X-RateLimit-Interval-Milliseconds.
        See: https://help.gohighlevel.com/support/solutions/articles/48001060529
        """
        interval_ms = int(
            headers.get("x-ratelimit-interval-milliseconds")
            or headers.get("x-ratelimit-interval-ms")
            or 10000
        )
        reset = None
        reset_val = headers.get("x-ratelimit-reset")
        if reset_val:
            try:
                t = float(reset_val)
                if t > 0:
                    reset = t
            except (TypeError, ValueError):
                pass

        return cls(
            limit=int(
                headers.get("x-ratelimit-max")
                or headers.get("x-ratelimit-limit")
                or 100
            ),
            remaining=int(
                headers.get("x-ratelimit-remaining") or 100
            ),
            reset=reset,
            interval_ms=interval_ms,
        )


class APIError(Exception):
    """API error with status code and message."""

    def __init__(self, status_code: int, message: str, response_body: Optional[dict] = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class GHLClient:
    """HTTP client for GoHighLevel API with rate limiting."""

    BASE_URL = "https://services.leadconnectorhq.com"

    def __init__(self, token: str, location_id: Optional[str] = None):
        self.token = token
        self.location_id = location_id or config_manager.get_location_id()
        self.api_version = config_manager.config.api_version
        self._rate_limit_info: Optional[RateLimitInfo] = None
        self._client: Optional[httpx.Client] = None

    @property
    def rate_limit_info(self) -> Optional[RateLimitInfo]:
        """Latest rate limit info from API response headers (for TUI display)."""
        return self._rate_limit_info

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                headers=self._default_headers(),
                timeout=30.0,
            )
        return self._client

    def _default_headers(self) -> dict[str, str]:
        """Get default headers for all requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Update rate limit info and sleep if needed."""
        # Only update from response when it includes rate limit headers; some GHL
        # endpoints (e.g. customFields, customValues) don't return them, and we'd
        # otherwise overwrite good info with defaults (100/100).
        if RateLimitInfo.has_rate_limit_headers(response.headers):
            self._rate_limit_info = RateLimitInfo.from_headers(response.headers)

        if response.status_code == 429:
            # Rate limited - wait and retry
            rli = self._rate_limit_info or RateLimitInfo.from_headers(response.headers)
            wait_time = rli.interval_ms / 1000.0
            if rli.reset:
                wait_time = max(wait_time, rli.reset - time.time())
            time.sleep(wait_time + 0.1)  # Add small buffer
            return

        # Proactively slow down if near limit
        if self._rate_limit_info and self._rate_limit_info.remaining < 5:
            time.sleep(0.5)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising errors as needed."""
        self._handle_rate_limit(response)

        if response.status_code == 429:
            raise APIError(429, "Rate limited. Please wait and try again.")

        if response.status_code >= 400:
            body: Optional[dict] = None
            try:
                body = response.json()
                message = (body or {}).get("message") or (body or {}).get("error") or str(body)
            except Exception:
                message = response.text or f"HTTP {response.status_code}"
            raise APIError(response.status_code, message, body)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except Exception:
            return {"text": response.text}

    def request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
        max_retries: int = 3,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """
        Make an API request with automatic retry for rate limits.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path (e.g., "/contacts/")
            params: Query parameters
            json: JSON body
            files: Files to upload
            max_retries: Maximum number of retries for rate limits
            include_location_id: If True, add location to query params (False for nested routes)
            location_param: Key for location ("locationId" or "location_id")

        Returns:
            Response JSON as dict
        """
        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        # Add location if requested. Endpoints use "locationId" or "location_id".
        if include_location_id and self.location_id:
            if params is None:
                params = {}
            if location_param not in params:
                params[location_param] = self.location_id

        for attempt in range(max_retries):
            try:
                if files:
                    # For file uploads, don't use JSON content type
                    headers = self._default_headers()
                    del headers["Content-Type"]
                    response = self.client.request(
                        method,
                        path,
                        params=params,
                        data=json,  # Use form data with files
                        files=files,
                        headers=headers,
                    )
                else:
                    response = self.client.request(
                        method,
                        path,
                        params=params,
                        json=json,
                    )

                return self._handle_response(response)

            except APIError as e:
                if e.status_code == 429 and attempt < max_retries - 1:
                    continue  # Retry after rate limit sleep
                raise

        raise RuntimeError("Exhausted retries")  # Unreachable; satisfies type checker

    def get(
        self,
        path: str,
        params: Optional[dict] = None,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """Make a GET request."""
        return self.request(
            "GET",
            path,
            params=params,
            include_location_id=include_location_id,
            location_param=location_param,
        )

    def post(
        self,
        path: str,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self.request(
            "POST",
            path,
            json=json,
            files=files,
            include_location_id=include_location_id,
            location_param=location_param,
        )

    def put(
        self,
        path: str,
        json: Optional[dict] = None,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return self.request(
            "PUT",
            path,
            json=json,
            include_location_id=include_location_id,
            location_param=location_param,
        )

    def delete(
        self,
        path: str,
        params: Optional[dict] = None,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return self.request(
            "DELETE",
            path,
            params=params,
            include_location_id=include_location_id,
            location_param=location_param,
        )

    def patch(
        self,
        path: str,
        json: Optional[dict] = None,
        *,
        include_location_id: bool = True,
        location_param: Literal["locationId", "location_id"] = "locationId",
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return self.request(
            "PATCH",
            path,
            json=json,
            include_location_id=include_location_id,
            location_param=location_param,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "GHLClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
