# Example PHP API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta using a simple PHP script.

## Prerequisites

On macOS the required tools can be installed with [Homebrew](https://brew.sh):

```
brew install php composer node openjdk
```

This provides PHP 8.5 (the client requires PHP 8.1+) and Composer. `node` and `openjdk` are only needed to run [generate.sh](./generate.sh), as the openapi-generator-cli is a Node wrapper around a Java tool.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the calls `$config->setCertFile` and `$config->setKeyFile` in [example.php](./api-client/example.php) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
composer install
php example.php
```

## Code generation

The PHP API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

The generation script takes the API version and the spec name as arguments, e.g. `./generate.sh 4.0.2 beef` (the defaults). The spec is downloaded from `https://docs.aiaplatform.com.au/api/<version>/<name>.json`, so `openapi` generates a client for every endpoint.

The PHP generator flattens each `oneOf` into a single model, so [generate.sh](./generate.sh) adjusts the downloaded spec before generating: `const` values, `enum`s on `oneOf` variant properties, `pattern`s on date fields and "Empty object" `oneOf` branches are removed. The flattened models cannot represent alternatives such as seasonal vs monthly cattle classes, so the example request is written as JSON and sent as-is. The generated client still handles mTLS, transport and the typed response.
