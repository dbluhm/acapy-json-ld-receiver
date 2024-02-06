"""Minimal reproducible example script.

This script is for you to use to reproduce a bug or demonstrate a feature.
"""
from typing import Mapping
import pytest

import json
from os import getenv

from controller import Controller
from controller.logging import logging_to_stdout
from controller.models import CredAttrSpec, V20CredExRecord, V20CredExRecordDetail, V20CredExRecordIndy, V20CredFilter, V20CredFilterIndy, V20CredOfferRequest, V20CredPreview, V20PresExRecord
from controller.protocols import (
    didexchange,
    indy_anoncred_credential_artifacts,
    indy_anoncred_onboard,
    indy_present_proof_v2,
)

ALICE = getenv("ALICE", "http://alice:3001")
BOB = getenv("BOB", "http://bob:3001")


def summary(presentation: V20PresExRecord) -> str:
    """Summarize a presentation exchange record."""
    request = presentation.pres_request
    return "Summary: " + json.dumps(
        {
            "state": presentation.state,
            "verified": presentation.verified,
            "presentation_request": request.dict(by_alias=True) if request else None,
        },
        indent=2,
        sort_keys=True,
    )

async def indy_issue_credential_v2_issuer(
    issuer: Controller,
    issuer_connection_id: str,
    cred_def_id: str,
    attributes: Mapping[str, str],
) -> V20CredExRecordDetail:
    """Issue an indy credential using issue-credential/2.0."""

    issuer_cred_ex = await issuer.post(
        "/issue-credential-2.0/send-offer",
        json=V20CredOfferRequest(
            auto_issue=False,
            auto_remove=False,
            comment="Credential from minimal example",
            trace=False,
            connection_id=issuer_connection_id,
            filter=V20CredFilter(  # pyright: ignore
                indy=V20CredFilterIndy(  # pyright: ignore
                    cred_def_id=cred_def_id,
                )
            ),
            credential_preview=V20CredPreview(
                type="issue-credential-2.0/2.0/credential-preview",  # pyright: ignore
                attributes=[
                    CredAttrSpec(
                        mime_type=None, name=name, value=value  # pyright: ignore
                    )
                    for name, value in attributes.items()
                ],
            ),
        ),
        response=V20CredExRecord,
    )
    issuer_cred_ex_id = issuer_cred_ex.cred_ex_id

    await issuer.record_with_values(
        topic="issue_credential_v2_0",
        cred_ex_id=issuer_cred_ex_id,
        state="request-received",
    )

    issuer_cred_ex = await issuer.post(
        f"/issue-credential-2.0/records/{issuer_cred_ex_id}/issue",
        json={},
        response=V20CredExRecordDetail,
    )

    issuer_cred_ex = await issuer.record_with_values(
        topic="issue_credential_v2_0",
        record_type=V20CredExRecord,
        cred_ex_id=issuer_cred_ex_id,
        state="done",
    )
    issuer_indy_record = await issuer.record_with_values(
        topic="issue_credential_v2_0_indy",
        record_type=V20CredExRecordIndy,
    )

    return V20CredExRecordDetail(cred_ex_record=issuer_cred_ex, indy=issuer_indy_record)


@pytest.mark.asyncio
async def test_anoncreds():
    """Test Controller protocols."""
    logging_to_stdout()
    async with Controller(base_url=ALICE) as alice, Controller(base_url=BOB) as bob:
        # Connecting
        alice_conn, bob_conn = await didexchange(alice, bob)

        # Issuance prep
        await indy_anoncred_onboard(alice)
        _, cred_def = await indy_anoncred_credential_artifacts(
            alice,
            ["firstname", "lastname"],
            support_revocation=True,
        )

        # Issue a credential
        await indy_issue_credential_v2_issuer(
            alice,
            alice_conn.connection_id,
            cred_def.credential_definition_id,
            {"firstname": "Bob", "lastname": "Builder"},
        )

        # Present the the credential's attributes
        _, pres_ex_record = await indy_present_proof_v2(
            bob,
            alice,
            bob_conn.connection_id,
            alice_conn.connection_id,
            requested_attributes=[{"name": "firstname"}],
        )
        assert pres_ex_record.verified == "true"

