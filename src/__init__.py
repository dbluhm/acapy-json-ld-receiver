"""ACA-Py JSON-LD Receiver."""

from enum import Enum
from typing import Any

import fastapi
from fastapi.params import Body

from .models import (
    ConnRecord,
    InvitationRecord,
    IssuerCredRevRecord,
    IssuerRevRegRecord,
    MediationRecord,
    TransactionRecord,
    V10CredentialExchange,
    V10PresentationExchange,
    V20CredExRecord,
    V20PresExRecord,
)

tag_metadata = [
    {"name": "connections", "description": "Connection related webhooks"},
    {
        "name": "credentials",
        "description": "Credential and Presentation related webhooks",
    },
    {"name": "other", "description": "Miscellaneous webhooks"},
]

app = fastapi.FastAPI(openapi_tags=tag_metadata)


class Tags(Enum):
    """Tag names for OpenAPI documentation."""
    credentials = "credentials"
    connections = "connections"
    other = "other"


@app.post("/topic/connections", summary="Connection updates", tags=[Tags.connections])
@app.post("/topic/connections/", include_in_schema=False)
async def connections(body: ConnRecord):
    """Connections webhook."""
    print("connections topic called with:", body.json(indent=2))


@app.post(
    "/topic/oob_invitation", summary="Out-of-band updates", tags=[Tags.connections]
)
@app.post("/topic/oob_invitation", include_in_schema=False)
async def oob_invitation(body: InvitationRecord):
    """Out-of-band webhook."""
    print("oob_invitation topic called with:", body.json(indent=2))


@app.post("/topic/mediation", summary="Mediation updates", tags=[Tags.connections])
@app.post("/topic/mediation", include_in_schema=False)
async def mediation(body: MediationRecord):
    """Mediation webhook."""
    print("mediation topic called with:", body.json(indent=2))


@app.post(
    "/topic/revocation_registry",
    summary="Revocation registry updates",
    tags=[Tags.credentials],
)
@app.post("/topic/revocation_registry", include_in_schema=False)
async def revocation_registry(body: IssuerRevRegRecord):
    """Revocation registry webhook."""
    print("revocation_registry topic called with:", body.json(indent=2))


@app.post(
    "/topic/issuer_cred_rev",
    summary="Credential revocation updates (issuer)",
    tags=[Tags.credentials],
)
@app.post("/topic/issuer_cred_rev", include_in_schema=False)
async def issuer_cred_rev(body: IssuerCredRevRecord):
    """Issuer cred rev webhook."""
    print("issuer_cred_rev topic called with:", body.json(indent=2))


@app.post(
    "/topic/issue_credential",
    summary="Credential exchange updates",
    tags=[Tags.credentials],
)
@app.post("/topic/issue_credential", include_in_schema=False)
async def issue_credential(body: V10CredentialExchange):
    """ICv1 webhook."""
    print("issue_credential topic called with:", body.json(indent=2))


@app.post(
    "/topic/issue_credential_v2_0",
    summary="Credential exchange v2 updates",
    tags=[Tags.credentials],
)
@app.post("/topic/issue_credential_v2_0", include_in_schema=False)
async def issue_credential_v2_0(body: V20CredExRecord):
    """ICv2 webhook."""
    print("issue_credential_v2_0 topic called with:", body.json(indent=2))


@app.post(
    "/topic/present_proof",
    summary="Presentation exchange updates",
    tags=[Tags.credentials],
)
@app.post("/topic/present_proof", include_in_schema=False)
async def present_proof(body: V10PresentationExchange):
    """PPv1 webhook."""
    print("present_proof topic called with:", body.json(indent=2))


@app.post(
    "/topic/present_proof_v2_0",
    summary="Presentation exchange v2 updates",
    tags=[Tags.credentials],
)
@app.post("/topic/present_proof_v2_0", include_in_schema=False)
async def present_proof_v2_0(body: V20PresExRecord):
    """PPv2 webhook."""
    print("present_proof_v2_0 topic called with:", body.json(indent=2))


@app.post("/topic/discover_feature", summary="Discover Feature 1.0", tags=[Tags.other])
@app.post("/topic/discover_feature", include_in_schema=False)
async def discover_feature(body: Any):
    """Discover Features v1 webhook."""
    print("discover_feature topic called with:", body)


@app.post(
    "/topic/discover_feature_v2_0", summary="Discover Feature 2.0", tags=[Tags.other]
)
@app.post("/topic/discover_feature_v2_0", include_in_schema=False)
async def discover_feature_v2_0(body: Any):
    """Discover feature v2 webhook."""
    print("discover_feature_v2_0 topic called with:", body)


@app.post(
    "/topic/endorse_transaction",
    summary="Endorse Transaction updates",
    tags=[Tags.other],
)
@app.post("/topic/endorse_transaction", include_in_schema=False)
async def endorse_transaction(body: TransactionRecord):
    """Endorse transaction webhook."""
    print("endorse_transaction topic called with:", body.json(indent=2))


@app.post("/topic/{topic}")
async def webhook_received(topic: str, body: Any = Body(...)):
    """Catch-all webhook."""
    print(f"/topic/{topic}", body)
