import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tophost_dns_mcp.models import (
    APIHealth,
    DNSMutationResult,
    DNSRecord,
    DomainInfo,
)
from tophost_dns_mcp.server import build_server


class FakeAPI:
    def __init__(self):
        self.updated = None

    async def health(self):
        return APIHealth(status="ok")

    async def list_domains(self):
        return [
            DomainInfo(
                name="example.com",
                is_default=True,
            )
        ]

    async def list_records(
        self,
        *,
        domain,
        name=None,
        record_type=None,
        value=None,
    ):
        del name, record_type, value
        return [
            DNSRecord(
                id="1",
                name=domain,
                type="A",
                value="192.0.2.1",
                priority=0,
            )
        ]

    async def get_record(
        self,
        *,
        domain,
        record_id,
    ):
        return DNSRecord(
            id=record_id,
            name=domain,
            type="A",
            value="192.0.2.1",
            priority=0,
        )

    async def create_record(self, **kwargs):
        return DNSMutationResult(
            changed=True,
            after=DNSRecord(
                id="2",
                name=kwargs["name"],
                type=kwargs["record_type"],
                value=kwargs["value"],
                priority=kwargs["priority"],
            ),
        )

    async def update_record(self, **kwargs):
        self.updated = kwargs
        return DNSMutationResult(changed=True)

    async def delete_record(self, **kwargs):
        return DNSMutationResult(changed=True)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_server_exposes_expected_tools():
    server = build_server(FakeAPI())

    tools = {
        tool.name: tool
        for tool in await server.list_tools()
    }

    assert set(tools) == {
        "tophost_api_health",
        "list_domains",
        "list_dns_records",
        "get_dns_record",
        "create_dns_record",
        "update_dns_record",
        "delete_dns_record",
    }

    assert tools["list_domains"].annotations.read_only_hint is True
    assert tools["create_dns_record"].annotations.destructive_hint is False
    assert tools["delete_dns_record"].annotations.destructive_hint is True


@pytest.mark.anyio
async def test_update_requires_new_state_and_forwards_guard():
    api = FakeAPI()
    server = build_server(api)

    with pytest.raises(
        ToolError,
        match="At least one of value or priority",
    ):
        await server.call_tool(
            "update_dns_record",
            {
                "domain": "example.com",
                "record_id": "1",
                "expected_value": "192.0.2.1",
                "expected_priority": 0,
            },
        )

    result = await server.call_tool(
        "update_dns_record",
        {
            "domain": "example.com",
            "record_id": "1",
            "expected_value": "192.0.2.1",
            "expected_priority": 0,
            "value": "192.0.2.2",
        },
    )

    assert result.is_error is False
    assert api.updated == {
        "domain": "example.com",
        "record_id": "1",
        "expected_value": "192.0.2.1",
        "expected_priority": 0,
        "value": "192.0.2.2",
        "priority": None,
    }
