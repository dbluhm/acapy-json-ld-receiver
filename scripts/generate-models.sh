#!/usr/bin/env bash
set -e

cd "$(dirname "$0")" || exit

CONTAINER_RUNTIME=${CONTAINER_RUNTIME:-docker}
NAME="datamodel-codegen"
API_URL="https://raw.githubusercontent.com/Indicio-tech/acapy-openapi/main/openapi.yml"

${CONTAINER_RUNTIME} build -t ${NAME} - << DOCKERFILE
FROM python:3.7

WORKDIR /usr/src/app

RUN pip install datamodel-code-generator[http]==0.13.0

ENTRYPOINT ["datamodel-codegen"]
DOCKERFILE

${CONTAINER_RUNTIME} run --rm -it -v "$(realpath $(pwd)/../):/usr/src/app:z" ${NAME} \
    --url "${API_URL}" \
    --output ./src/models.py \
    --field-constraints \
    --use-schema-description \
    --reuse-model
