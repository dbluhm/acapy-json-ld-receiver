from enum import Enum
from os import getenv
from typing import Any, Optional

from controller import Controller
from controller.logging import logging_to_stdout
import fastapi
from fastapi.params import Body

from .models import (
    ConnRecord,
    DIDResult,
    InvitationRecord,
    IssuerCredRevRecord,
    IssuerRevRegRecord,
    MediationRecord,
    TransactionRecord,
    V10CredentialExchange,
    V10PresentationExchange,
    V20CredExRecord,
    V20CredExRecordDetail,
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

AGENT = getenv("AGENT", "http://localhost:3001")
did: Optional[str] = None


@app.on_event("startup")
async def on_startup():
    """Startup event."""
    logging_to_stdout()
    global did
    print("Creating did:key for agent: ", AGENT)
    controller = Controller(AGENT)
    result = await controller.post(
        "/wallet/did/create",
        json={"method": "key"},
        response=DIDResult,
    )
    assert result.result
    did = result.result.did


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

    controller = Controller(AGENT)
    cred_rec = body
    if not cred_rec.by_format:
        cred_rec = (await controller.get(
            f"/issue-credential-2.0/records/{cred_rec.cred_ex_id}",
            response=V20CredExRecordDetail,
        )).cred_ex_record
        assert cred_rec

    if cred_rec.state == "offer-received":
        print("Received credential offer, sending credential request")

        if not cred_rec.by_format:
            cred_rec = (await controller.get(
                f"/issue-credential-2.0/records/{cred_rec.cred_ex_id}",
                response=V20CredExRecordDetail,
            )).cred_ex_record
            assert cred_rec
        assert cred_rec.by_format
        if not cred_rec.by_format.cred_offer:
            raise ValueError("Expected credential offer by format")

        cred_request = await controller.post(
            f"/issue-credential-2.0/records/{cred_rec.cred_ex_id}/send-request",
            json={"holder_did": did} if "ld_proof" in cred_rec.by_format.cred_offer else {}
        )
        print("Credential request sent:", cred_request)
    elif cred_rec.state == "credential-received":
        if cred_rec.cred_issue:
            print("Received credential:", cred_rec.cred_issue.json(indent=2))
        else:
            print("Received credential with id:", cred_rec.cred_ex_id)

        await controller.post(
            f"/issue-credential-2.0/records/{cred_rec.cred_ex_id}/store",
        )
        print("Credential stored.")
    else:
        print("Taking no action.")


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
