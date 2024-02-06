# ACA-Py JSON-LD Receiver

This is a simple controller that enables an ACA-Py instance to use a did:key as
the holder DID for JSON-LD Credential Issuance requests. It will also auto
respond to AnonCreds credential offers.

## Usage

This controller requires:

- The ACA-Py instance must be started and accissble before the controller starts.
- `--debug-webhooks` MUST be enabled (present or `true` in yaml config)
- `--auto-respond-credential-offer` MUST be disable (absent or `false` in yaml config)
- `--auto-store-credential` MUST be disabled (absent or `false` in yaml config)

### Docker Compose Usage

Supposing you had a docker-compose service named `bob` like the following:

```yaml
  bob:
    image: ghcr.io/hyperledger/aries-cloudagent-python:py3.9-0.10.5
    ports:
      - "3002:3001"
    command: >
      start -it http 0.0.0.0 3000
        --label Bob
        -ot http
        -e http://bob:3000
        --admin 0.0.0.0 3001 --admin-insecure-mode
        --log-level debug
        --genesis-url https://raw.githubusercontent.com/Indicio-tech/indicio-network/main/genesis_files/pool_transactions_demonet_genesis
        --webhook-url http://bob-controller
        --wallet-type askar
        --wallet-name bob
        --wallet-key insecure
        --auto-provision
        --debug-webhooks
    healthcheck:
      test: curl -s -o /dev/null -w '%{http_code}' "http://localhost:3001/status/live" | grep "200" > /dev/null
      start_period: 30s
      interval: 3s
      timeout: 5s
      retries: 5
```

You can use this controller using a service like the following:

```yaml
  bob-controller:
    image: ghcr.io/dbluhm/acapy-json-ld-receiver:0.1.0
    environment:
      AGENT: http://bob:3001
    depends_on:
      bob:
        condition: service_healthy
```

### Building and Running

```sh
$ docker build -t acapy-webhook .
$ docker run --rm -it -p 8080:80 -e AGENT=http://localhost:3001 acapy-webhook
```

Navigate to http://localhost:8080/docs in the browser.
