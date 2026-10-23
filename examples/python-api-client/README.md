# Example Python API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta using a simple Python script.

## Prerequisites

On macOS the required tools can be installed with [Homebrew](https://brew.sh):

```
brew install python node openjdk
```

This provides Python 3 (3.9+ is required). `node` and `openjdk` are only needed to run [generate.sh](./generate.sh), as the openapi-generator-cli is a Node wrapper around a Java tool.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the parameters `cert_file="cert.pem"` and `key_file="key.pem"` in [test_api.py](./api-client/test_api.py) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
setup_local.sh
run_test.sh
```

## Code generation

The Python API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

The generation script takes the API version as an argument, e.g. `./generate.sh 4.0.2` (the default).

Before generating, [generate.sh](./generate.sh) removes "Empty object" `oneOf` branches from the downloaded spec, because the Python generator maps them to a plain object that matches any input.

**Temporary:** `gas` is also made optional on `OutputMethod1`/`OutputMethod2`, because the API currently omits it from some outputs (such as `scope3.services`). This should be removed once the API or spec is fixed.
