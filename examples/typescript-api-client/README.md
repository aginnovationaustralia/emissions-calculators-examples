# Example TypeScript API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta using a simple TypeScript script.

## Prerequisites

On macOS the required tools can be installed with [Homebrew](https://brew.sh):

```
brew install node openjdk
```

This provides Node.js and npm, which are needed both to run the example and to generate the client. `openjdk` is only needed to run [generate.sh](./generate.sh), as the openapi-generator-cli is a Node wrapper around a Java tool.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the values for `certFile` and `keyFile` in [test_api.ts](./api-client/test_api.ts) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
setup_local.sh
run_test.sh
```

## Code generation

The TypeScript API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

The generation script takes the API version and the spec name as arguments, e.g. `./generate.sh 4.0.2 beef` (the defaults). The spec is downloaded from `https://docs.aiaplatform.com.au/api/<version>/<name>.json`, so `openapi` generates a client for every endpoint.

A customised [modelOneOf.mustache](./templates/modelOneOf.mustache) template adds the `instanceOf` check that the generator omits for `oneOf` models, which is needed to serialise nested `oneOf` values.
