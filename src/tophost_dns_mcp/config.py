from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration for the MCP-to-REST bridge."""

    api_url: str = "http://127.0.0.1:8765"
    api_key: str | None = None
    request_timeout: float = 20.0

    @classmethod
    def from_env(cls) -> Settings:
        raw_timeout = os.getenv("TOPHOST_MCP_REQUEST_TIMEOUT", "20")

        try:
            timeout = float(raw_timeout)
        except ValueError as exc:
            raise ValueError(
                "TOPHOST_MCP_REQUEST_TIMEOUT must be a number"
            ) from exc

        if timeout <= 0:
            raise ValueError(
                "TOPHOST_MCP_REQUEST_TIMEOUT must be greater than zero"
            )

        api_url = os.getenv(
            "TOPHOST_DNS_API_URL",
            "http://127.0.0.1:8765",
        ).strip()

        if not api_url:
            raise ValueError("TOPHOST_DNS_API_URL cannot be empty")

        return cls(
            api_url=api_url.rstrip("/"),
            api_key=os.getenv("TOPHOST_API_KEY"),
            request_timeout=timeout,
        )
