# Tophost DNS MCP

MCP server for the unofficial
[Tophost DNS API](https://github.com/DanielVd/tophost-dns-api).

> This project is unofficial and is not affiliated with, endorsed by, or
> supported by Tophost.

The server exposes the DNS operations implemented by `tophost-dns-api` as
Model Context Protocol tools. It does **not** talk to the Tophost control panel
directly.

```text
MCP client / AI agent
        |
        v
Tophost DNS MCP
        |
        v
Tophost DNS API
        |
        v
Tophost
```

The separation is intentional: Tophost authentication, trusted 2FA, product
discovery, HTML parsing and DNS protocol details remain inside
`tophost-dns-api`. This repository is only the MCP tool layer.

## Status

Initial implementation. The package targets the current stable v2 line of the
official Python MCP SDK.

## Requirements

- Python 3.11 or newer
- a running `tophost-dns-api` instance
- the API key configured by that instance

## Installation

```bash
git clone https://github.com/DanielVd/tophost-dns-mcp.git
cd tophost-dns-mcp

python -m venv .venv
. .venv/bin/activate

pip install -e .
```

For development:

```bash
pip install -e '.[dev]'
```

## Configuration

```bash
export TOPHOST_DNS_API_URL=http://127.0.0.1:8765
export TOPHOST_API_KEY='replace-me'
```

Optional:

```bash
export TOPHOST_MCP_REQUEST_TIMEOUT=20
```

The MCP process does not need `TOPHOST_USER`, `TOPHOST_PASS`, OTP values or
trusted 2FA state. Those remain configured only in `tophost-dns-api`.

## Running

The default transport is stdio:

```bash
tophost-dns-mcp
```

For Streamable HTTP:

```bash
tophost-dns-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000
```

The MCP endpoint is the SDK default, `/mcp`.

For development with the MCP Inspector:

```bash
mcp dev src/tophost_dns_mcp/server.py:mcp
```

## Tools

| Tool | Mutation | Purpose |
| --- | --- | --- |
| `tophost_api_health` | no | Check REST API reachability |
| `list_domains` | no | List domains available to the account |
| `list_dns_records` | no | List/filter DNS records |
| `get_dns_record` | no | Read one record by current record ID |
| `create_dns_record` | yes | Create a record; identical records are a no-op |
| `update_dns_record` | yes | Update with mandatory expected-state guards |
| `delete_dns_record` | yes | Delete with mandatory expected-state guards |

Read-only and mutation tools include MCP tool annotations. These annotations are
client hints only; they are not treated as an authorization mechanism.

## Mutation safety

The MCP layer deliberately makes update and delete stricter than the REST API.

Before updating or deleting a record, first read it and pass both
`expected_value` and `expected_priority` back to the mutation tool. The REST
API verifies that the record has not changed in the meantime and refuses a stale
mutation.

The underlying API can change a Tophost record ID after an update. Always use the
ID returned in the mutation result for subsequent operations.

## Error handling

REST API application errors are converted into MCP tool errors with the stable
error code and message returned by `tophost-dns-api`.

Raw HTML, response bodies, API keys and authentication material are not included
in tool errors.

## Development

```bash
ruff check src tests
pytest -q
```

## Related project

REST API and Tophost protocol implementation:

https://github.com/DanielVd/tophost-dns-api

## License

MIT. See [LICENSE](LICENSE).
