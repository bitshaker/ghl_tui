"""HTTP client for GoHighLevel API."""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from .config import config_manager


class RateLimitInfo(BaseModel):
    """Rate limit information from API response headers."""

    limit: int = 100
    remaining: int = 100
    reset: Optional[float] = None
    interval_ms: int = 10000

    @classmethod
    def from_headers(cls, headers: httpx.Headers) -> "RateLimitInfo":
        """Parse rate limit info from response headers."""
        return cls(
            limit=int(headers.get("x-ratelimit-limit", 100)),
            remaining=int(headers.get("x-ratelimit-remaining", 100)),
            reset=float(headers.get("x-ratelimit-reset", 0)) or None,
            interval_ms=int(headers.get("x-ratelimit-interval-ms", 10000)),
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
        self._rate_limit_info = RateLimitInfo.from_headers(response.headers)

        if response.status_code == 429:
            # Rate limited - wait and retry
            wait_time = self._rate_limit_info.interval_ms / 1000.0
            if self._rate_limit_info.reset:
                wait_time = max(wait_time, self._rate_limit_info.reset - time.time())
            time.sleep(wait_time + 0.1)  # Add small buffer
            return

        # Proactively slow down if near limit
        if self._rate_limit_info.remaining < 5:
            time.sleep(0.5)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising errors as needed."""
        self._handle_rate_limit(response)

        if response.status_code == 429:
            raise APIError(429, "Rate limited. Please wait and try again.")

        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("message") or body.get("error") or str(body)
            except Exception:
                message = response.text or f"HTTP {response.status_code}"
            raise APIError(response.status_code, message, body if "body" in dir() else None)

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

        Returns:
            Response JSON as dict
        """
        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        # Add location ID to params if available and not already present
        if self.location_id and params is not None:
            if "locationId" not in params:
                params["locationId"] = self.location_id
        elif self.location_id and params is None:
            params = {"locationId": self.location_id}

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

    def get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params)

    def post(
        self, path: str, json: Optional[dict] = None, files: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, json=json, files=files)

    def put(self, path: str, json: Optional[dict] = None) -> dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json)

    def delete(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, params=params)

    def patch(self, path: str, json: Optional[dict] = None) -> dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", path, json=json)

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "GHLClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
