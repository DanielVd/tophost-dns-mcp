# Tophost DNS MCP

MCP server for the unofficial [Tophost DNS API](https://github.com/DanielVd/tophost-dns-api).

> **Work in progress**
>
> This repository is public so development can be followed from the beginning.
> There is no functional MCP server release yet.

This project will provide a Model Context Protocol (MCP) interface on top of
`tophost-dns-api`, allowing compatible MCP clients and AI agents to work with
Tophost DNS through a structured tool layer.

The MCP server is intentionally designed **not** to reverse engineer or call the
Tophost control panel directly. Tophost-specific authentication, 2FA, product
discovery, HTML parsing and DNS mutations remain isolated in the REST API
project.

## Planned architecture

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
Service layer
        |
        v
Tophost
```

## Planned scope

The initial MCP implementation is expected to expose the DNS capabilities
already provided by `tophost-dns-api`, including domain discovery, DNS record
inspection and controlled DNS mutations.

Destructive operations will preserve the safety properties of the underlying
API, including optimistic concurrency checks where applicable.

The exact MCP tools and schemas will be documented only as they are implemented.

## Related project

The underlying REST API is available here:

https://github.com/DanielVd/tophost-dns-api

Current public release: `v0.1.0`.

## Status

Development has started. No MCP release has been published yet.

## Disclaimer

This is an unofficial project and is not affiliated with, endorsed by, or
supported by Tophost.
