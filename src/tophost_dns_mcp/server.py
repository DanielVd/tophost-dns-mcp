from __future__ import annotations

import argparse
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from tophost_dns_mcp.client import TophostDNSAPIClient
from tophost_dns_mcp.config import Settings
from tophost_dns_mcp.models import (
    APIHealth,
    DNSMutationResult,
    DNSRecord,
    DomainInfo,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]
Priority = Annotated[int, Field(ge=0, le=65535)]
OptionalPriority = Annotated[int | None, Field(ge=0, le=65535)]

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    idempotent_hint=True,
    open_world_hint=True,
)

CREATE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)

MUTATE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=True,
)


def build_server(
    api: TophostDNSAPIClient | None = None,
) -> MCPServer:
    """Build the MCP server around one Tophost DNS API client."""

    api = api or TophostDNSAPIClient(
        Settings.from_env()
    )
    server = MCPServer("Tophost DNS MCP")

    @server.tool(
        title="Tophost DNS API health",
        description=(
            "Check whether the configured Tophost DNS REST API "
            "process is reachable."
        ),
        annotations=READ_ONLY,
    )
    async def tophost_api_health() -> APIHealth:
        return await api.health()

    @server.tool(
        title="List Tophost domains",
        description=(
            "List domains discovered by the authenticated "
            "Tophost DNS API account."
        ),
        annotations=READ_ONLY,
    )
    async def list_domains() -> list[DomainInfo]:
        return await api.list_domains()

    @server.tool(
        title="List DNS records",
        description=(
            "List DNS records for one Tophost domain. Optional "
            "name, type and value filters can be combined."
        ),
        annotations=READ_ONLY,
    )
    async def list_dns_records(
        domain: NonEmptyStr,
        name: str | None = None,
        record_type: str | None = None,
        value: str | None = None,
    ) -> list[DNSRecord]:
        return await api.list_records(
            domain=domain,
            name=name,
            record_type=record_type,
            value=value,
        )

    @server.tool(
        title="Get DNS record",
        description=(
            "Read one DNS record by its current Tophost record ID."
        ),
        annotations=READ_ONLY,
    )
    async def get_dns_record(
        domain: NonEmptyStr,
        record_id: NonEmptyStr,
    ) -> DNSRecord:
        return await api.get_record(
            domain=domain,
            record_id=record_id,
        )

    @server.tool(
        title="Create DNS record",
        description=(
            "Create a DNS record. The underlying API treats an "
            "already-identical record as a no-op."
        ),
        annotations=CREATE,
    )
    async def create_dns_record(
        domain: NonEmptyStr,
        name: NonEmptyStr,
        record_type: NonEmptyStr,
        value: NonEmptyStr,
        priority: Priority = 0,
    ) -> DNSMutationResult:
        return await api.create_record(
            domain=domain,
            name=name,
            record_type=record_type.strip().upper(),
            value=value,
            priority=priority,
        )

    @server.tool(
        title="Update DNS record",
        description=(
            "Update a DNS record using expected_value and "
            "expected_priority as mandatory optimistic-concurrency "
            "guards. Read the record first and pass the observed state."
        ),
        annotations=MUTATE,
    )
    async def update_dns_record(
        domain: NonEmptyStr,
        record_id: NonEmptyStr,
        expected_value: str,
        expected_priority: Priority,
        value: str | None = None,
        priority: OptionalPriority = None,
    ) -> DNSMutationResult:
        if value is None and priority is None:
            raise ToolError(
                "At least one of value or priority must be supplied"
            )

        return await api.update_record(
            domain=domain,
            record_id=record_id,
            expected_value=expected_value,
            expected_priority=expected_priority,
            value=value,
            priority=priority,
        )

    @server.tool(
        title="Delete DNS record",
        description=(
            "Delete a DNS record using mandatory expected_value "
            "and expected_priority optimistic-concurrency guards. "
            "Read the record first and pass the observed state."
        ),
        annotations=MUTATE,
    )
    async def delete_dns_record(
        domain: NonEmptyStr,
        record_id: NonEmptyStr,
        expected_value: str,
        expected_priority: Priority,
    ) -> DNSMutationResult:
        return await api.delete_record(
            domain=domain,
            record_id=record_id,
            expected_value=expected_value,
            expected_priority=expected_priority,
        )

    return server


mcp = build_server()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP server for the unofficial Tophost DNS API"
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind address for streamable-http",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port for streamable-http",
    )

    args = parser.parse_args()

    transport: Literal["stdio", "streamable-http"] = args.transport

    if transport == "stdio":
        mcp.run()
        return

    mcp.run(
        "streamable-http",
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
