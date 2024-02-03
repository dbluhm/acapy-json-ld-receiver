#!/usr/bin/env bash
set -e

cd "$(dirname "$0")" || exit

CONTAINER_RUNTIME=${CONTAINER_RUNTIME:-docker}
WAIT_INTERVAL=${WAIT_INTERVAL:-3}
WAIT_ATTEMPTS=${WAIT_ATTEMPTS:-10}

IMAGE="acapy-webhook"
NAME="acapy-webhook-$(env LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 16 | head -n 1)"
URL="http://${DOCKER_CONTAINER_HOST:-localhost}:8080/openapi.json"

${CONTAINER_RUNTIME} build -t ${IMAGE} ..
${CONTAINER_RUNTIME} run --rm -d --name "${NAME}" -p 8080:80 ${IMAGE}
trap '${CONTAINER_RUNTIME} kill ${NAME}' EXIT

SUCCESS=0
for _ in $(seq 1 "$WAIT_ATTEMPTS"); do
    if ! wget --server-response --spider --quiet ${URL} 2>&1 | grep "200 OK" > /dev/null; then
        echo "Waiting for server..." 1>&2
        sleep "$WAIT_INTERVAL" &
        wait $!
    else
        SUCCESS=1
        break
    fi
done

if [[ $SUCCESS -eq 0 ]]; then
    echo "Failed to retrieve openapi.json from server"
    exit 1
fi

wget ${URL} -O ../openapi.json
