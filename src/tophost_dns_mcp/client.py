from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from tophost_dns_mcp.config import Settings
from tophost_dns_mcp.models import (
    APIHealth,
    DNSMutationResult,
    DNSRecord,
    DomainInfo,
)


class TophostDNSAPIClient:
    """Small async client for the public tophost-dns-api REST contract."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.settings = settings
        self.transport = transport

    async def health(self) -> APIHealth:
        data = await self._request(
            "GET",
            "/health",
            authenticated=False,
        )
        return self._model(APIHealth, data)

    async def list_domains(self) -> list[DomainInfo]:
        data = await self._request("GET", "/v1/domains")

        if not isinstance(data, list):
            raise ToolError(
                "Tophost DNS API returned an unexpected domains response"
            )

        return [
            self._model(DomainInfo, item)
            for item in data
        ]

    async def list_records(
        self,
        *,
        domain: str,
        name: str | None = None,
        record_type: str | None = None,
        value: str | None = None,
    ) -> list[DNSRecord]:
        params = {
            key: item
            for key, item in {
                "name": name,
                "type": record_type,
                "value": value,
            }.items()
            if item is not None
        }

        data = await self._request(
            "GET",
            self._records_path(domain),
            params=params,
        )

        if not isinstance(data, list):
            raise ToolError(
                "Tophost DNS API returned an unexpected DNS records response"
            )

        return [
            self._model(DNSRecord, item)
            for item in data
        ]

    async def get_record(
        self,
        *,
        domain: str,
        record_id: str,
    ) -> DNSRecord:
        data = await self._request(
            "GET",
            f"{self._records_path(domain)}/{quote(record_id, safe='')}",
        )
        return self._model(DNSRecord, data)

    async def create_record(
        self,
        *,
        domain: str,
        name: str,
        record_type: str,
        value: str,
        priority: int,
    ) -> DNSMutationResult:
        data = await self._request(
            "POST",
            self._records_path(domain),
            json={
                "name": name,
                "type": record_type,
                "value": value,
                "priority": priority,
            },
        )
        return self._model(DNSMutationResult, data)

    async def update_record(
        self,
        *,
        domain: str,
        record_id: str,
        expected_value: str,
        expected_priority: int,
        value: str | None,
        priority: int | None,
    ) -> DNSMutationResult:
        payload: dict[str, Any] = {
            "expected_value": expected_value,
            "expected_priority": expected_priority,
        }

        if value is not None:
            payload["value"] = value

        if priority is not None:
            payload["priority"] = priority

        data = await self._request(
            "PATCH",
            f"{self._records_path(domain)}/{quote(record_id, safe='')}",
            json=payload,
        )
        return self._model(DNSMutationResult, data)

    async def delete_record(
        self,
        *,
        domain: str,
        record_id: str,
        expected_value: str,
        expected_priority: int,
    ) -> DNSMutationResult:
        data = await self._request(
            "DELETE",
            f"{self._records_path(domain)}/{quote(record_id, safe='')}",
            params={
                "expected_value": expected_value,
                "expected_priority": expected_priority,
            },
        )
        return self._model(DNSMutationResult, data)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        headers: dict[str, str] = {}

        if authenticated:
            if not self.settings.api_key:
                raise ToolError(
                    "TOPHOST_API_KEY is not configured for tophost-dns-mcp"
                )

            headers["X-API-Key"] = self.settings.api_key

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.api_url,
                headers=headers,
                timeout=self.settings.request_timeout,
                transport=self.transport,
            ) as client:
                response = await client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                )
        except httpx.TimeoutException as exc:
            raise ToolError(
                "Tophost DNS API request timed out"
            ) from exc
        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to reach the Tophost DNS API"
            ) from exc

        if response.status_code >= 400:
            raise self._api_error(response)

        try:
            return response.json()
        except ValueError as exc:
            raise ToolError(
                "Tophost DNS API returned a non-JSON response"
            ) from exc

    @staticmethod
    def _api_error(response: httpx.Response) -> ToolError:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            error = payload.get("error")

            if isinstance(error, dict):
                code = error.get("code")
                message = error.get("message")
                retryable = error.get("retryable")

                if isinstance(code, str) and isinstance(message, str):
                    suffix = " (retryable)" if retryable is True else ""
                    return ToolError(
                        f"{code}: {message}{suffix}"
                    )

        return ToolError(
            "Tophost DNS API returned "
            f"HTTP {response.status_code}"
        )

    @staticmethod
    def _model(model_type, data):
        try:
            return model_type.model_validate(data)
        except ValidationError as exc:
            raise ToolError(
                "Tophost DNS API returned an unexpected response shape"
            ) from exc

    @staticmethod
    def _records_path(domain: str) -> str:
        return (
            f"/v1/domains/{quote(domain, safe='')}"
            "/dns/records"
        )
