"""Minimal reproducible example script.

This script is for you to use to reproduce a bug or demonstrate a feature.
"""
import pytest

from datetime import date
import json
from os import getenv
from uuid import uuid4

from controller import Controller
from controller.logging import logging_to_stdout, section
from controller.models import DIDResult, LDProofVCDetail, V20CredExFree, V20CredExRecord, V20CredFilter, V20PresExRecord
from controller.protocols import (
    didexchange,
    indy_anoncred_onboard,
    jsonld_present_proof,
)

ALICE = getenv("ALICE", "http://alice:3001")
BOB = getenv("BOB", "http://bob:3001")


def presentation_summary(pres_ex: V20PresExRecord):
    """Summarize a presentation."""
    pres_ex_dict = pres_ex.dict(exclude_none=True, exclude_unset=True)
    return json.dumps(
        {
            key: pres_ex_dict.get(key)
            for key in (
                "verified",
                "state",
                "role",
                "connection_id",
                "pres_request",
                "pres",
            )
        },
        indent=2,
    )


@pytest.mark.asyncio
async def test_json_ld():
    """Test Controller protocols."""
    logging_to_stdout()

    async with Controller(base_url=ALICE) as alice, Controller(base_url=BOB) as bob:
        with section("Establish connection"):
            alice_conn, bob_conn = await didexchange(alice, bob)

        with section("Prepare for issuance"):
            with section("Issuer prepares issuing DIDs", character="-"):
                public_did = await indy_anoncred_onboard(alice)
                bls_alice_did = (
                    await alice.post(
                        "/wallet/did/create",
                        json={"method": "key", "options": {"key_type": "bls12381g2"}},
                        response=DIDResult,
                    )
                ).result
                assert bls_alice_did

        with section("Issue example credential using ED25519 Signature"):
            credential = {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://w3id.org/citizenship/v1",
                ],
                "type": ["VerifiableCredential", "PermanentResident"],
                "issuer": "did:sov:" + public_did.did,
                "issuanceDate": str(date.today()),
                "credentialSubject": {
                    "type": ["PermanentResident"],
                    "givenName": "Bob",
                    "familyName": "Builder",
                    "gender": "Male",
                    "birthCountry": "Bahamas",
                    "birthDate": "1958-07-17",
                }
            }
            options={"proofType": "Ed25519Signature2018"}
            issuer_cred_ex = await alice.post(
                "/issue-credential-2.0/send",
                json=V20CredExFree(
                    auto_remove=False,
                    comment="Credential from minimal example",
                    trace=False,
                    connection_id=alice_conn.connection_id,
                    filter=V20CredFilter(  # pyright: ignore
                        ld_proof=LDProofVCDetail.parse_obj({
                            "credential": credential,
                            "options": options,
                        })
                    ),
                ),
                response=V20CredExRecord,
            )
            issuer_cred_ex = await alice.record_with_values(
                topic="issue_credential_v2_0",
                record_type=V20CredExRecord,
                cred_ex_id=issuer_cred_ex.cred_ex_id,
                state="done",
            )

        with section("Present example credential"):
            alice_pres_ex, _ = await jsonld_present_proof(
                alice,
                bob,
                alice_conn.connection_id,
                bob_conn.connection_id,
                presentation_definition={
                    "input_descriptors": [
                        {
                            "id": "citizenship_input_1",
                            "name": "EU Driver's License",
                            "schema": [
                                {
                                    "uri": "https://www.w3.org/2018/credentials#VerifiableCredential"  # noqa: E501
                                },
                                {
                                    "uri": "https://w3id.org/citizenship#PermanentResident"  # noqa: E501
                                },
                            ],
                            "constraints": {
                                "is_holder": [
                                    {
                                        "directive": "required",
                                        "field_id": [
                                            "1f44d55f-f161-4938-a659-f8026467f126"
                                        ],
                                    }
                                ],
                                "fields": [
                                    {
                                        "id": "1f44d55f-f161-4938-a659-f8026467f126",
                                        "path": ["$.credentialSubject.familyName"],
                                        "purpose": "The claim must be from one of the specified issuers",  # noqa: E501
                                        "filter": {"const": "Builder"},
                                    },
                                    {
                                        "path": ["$.credentialSubject.givenName"],
                                        "purpose": "The claim must be from one of the specified issuers",  # noqa: E501
                                    },
                                ],
                            },
                        }
                    ],
                    "id": str(uuid4()),
                    "format": {"ldp_vp": {"proof_type": ["Ed25519Signature2018"]}},
                },
                domain="test-degree",
            )

        with section("Presentation summary", character="-"):
            print(presentation_summary(alice_pres_ex))

        assert alice_pres_ex.verified == "true"
