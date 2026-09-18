from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class APIHealth(StrictModel):
    status: str


class DomainInfo(StrictModel):
    name: str
    is_default: bool = False


class DNSRecord(StrictModel):
    id: str
    name: str
    type: str
    value: str
    priority: int = 0


class DNSMutationResult(StrictModel):
    changed: bool
    before: DNSRecord | None = None
    after: DNSRecord | None = None
    dns_serial: str | None = None
    message: str | None = None
