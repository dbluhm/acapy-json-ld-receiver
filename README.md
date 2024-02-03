# Example ACA-Py Webhook Receiver

This is an example ACA-Py Webhook receiver. It is built using FastAPI and serves
as a good starting point for writing your own ACA-Py webhook processor.

## OpenAPI Spec for Webhooks

The other primary output of this repo is the [OpenAPI Spec](/openapi.json) which
details the topics emitted by ACA-Py and the expected payloads.

## Run the Webhook Receiver

```sh
$ docker build -t acapy-webhook .
$ docker run --rm -it -p 8080:80 acapy-webhook
```

Navigate to http://localhost:8080/docs in the browser.
