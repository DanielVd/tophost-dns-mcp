# Security Policy

## Scope

Tophost DNS MCP can invoke operations that change DNS records through a
configured `tophost-dns-api` instance. Treat the MCP server as privileged
infrastructure.

## Secrets

The MCP server needs only the REST API endpoint and its API key. Tophost account
credentials, OTP codes, cookies and trusted 2FA state belong to
`tophost-dns-api` and must not be copied into this project.

Never commit API keys or local environment files.

## Network exposure

The default transport is stdio.

If Streamable HTTP is enabled, the server binds to loopback by default. Do not
expose it directly to the Internet without appropriate transport authentication,
TLS and network access controls.

## Mutation safety

Update and delete tools require the record value and priority observed by the
caller before the mutation. These values are forwarded to `tophost-dns-api`
as optimistic-concurrency guards.

Tool annotations are hints for MCP clients and are not a security boundary.

## Reporting security issues

Do not disclose suspected vulnerabilities in a public issue. Use GitHub Private
Vulnerability Reporting when available, or contact the repository owner
privately through the contact details on their GitHub profile.
