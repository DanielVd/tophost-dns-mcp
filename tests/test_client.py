import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tophost_dns_mcp.client import TophostDNSAPIClient
from tophost_dns_mcp.config import Settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_list_domains_sends_api_key():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "secret"
        assert request.url.path == "/v1/domains"

        return httpx.Response(
            200,
            json=[
                {
                    "name": "example.com",
                    "is_default": True,
                }
            ],
        )

    client = TophostDNSAPIClient(
        Settings(
            api_url="http://api.test",
            api_key="secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    domains = await client.list_domains()

    assert len(domains) == 1
    assert domains[0].name == "example.com"
    assert domains[0].is_default is True


@pytest.mark.anyio
async def test_missing_api_key_is_a_tool_error():
    client = TophostDNSAPIClient(
        Settings(
            api_url="http://api.test",
            api_key=None,
        ),
    )

    with pytest.raises(
        ToolError,
        match="TOPHOST_API_KEY is not configured",
    ):
        await client.list_domains()


@pytest.mark.anyio
async def test_api_error_is_exposed_without_raw_body():
    def handler(request: httpx.Request) -> httpx.Response:
        del request

        return httpx.Response(
            409,
            json={
                "error": {
                    "code": "RECORD_CHANGED",
                    "message": "DNS record changed since it was read",
                    "retryable": False,
                    "context": {
                        "sensitive": "not included in message"
                    },
                }
            },
        )

    client = TophostDNSAPIClient(
        Settings(
            api_url="http://api.test",
            api_key="secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        ToolError,
        match=(
            "RECORD_CHANGED: DNS record changed since it was read"
        ),
    ) as exc_info:
        await client.delete_record(
            domain="example.com",
            record_id="123",
            expected_value="192.0.2.1",
            expected_priority=0,
        )

    assert "sensitive" not in str(exc_info.value)
