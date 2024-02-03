#!/usr/bin/env bash
set -e

cd "$(dirname "$0")" || exit

CONTAINER_RUNTIME=${CONTAINER_RUNTIME:-docker}
NAME="datamodel-codegen"
VERSION="${1:-main}"
if [ $# -gt 0 ]; then
    shift
fi
API_URL="${API_URL:-https://raw.githubusercontent.com/hyperledger/aries-cloudagent-python/${VERSION}/open-api/openapi.json}"

${CONTAINER_RUNTIME} build -t ${NAME} - << DOCKERFILE
FROM python:3.10

WORKDIR /usr/src/app

RUN pip install datamodel-code-generator[http]==0.25.1

ENTRYPOINT ["datamodel-codegen"]
DOCKERFILE

${CONTAINER_RUNTIME} run --rm -v "$(pwd)/../:/usr/src/app:z" ${NAME} \
    --url "${API_URL}" \
    --output ./src/models.py \
    --field-constraints \
    --use-schema-description \
    --enum-field-as-literal all \
    --reuse-model \
    --snake-case-field \
    --allow-population-by-field-name \
    --aliases ./scripts/aliases.json \
    $@
