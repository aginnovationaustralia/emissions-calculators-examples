# Example C# API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta using a simple C# script.

## Prerequisites

On macOS the required tools can be installed with [Homebrew](https://brew.sh):

```
brew install dotnet@9 node openjdk
brew link --force dotnet@9
```

The example targets `net9.0`, so it needs the .NET 9 SDK. `dotnet@9` is keg-only, so it has to be linked (or added to your `PATH`) before `dotnet` is available. The plain `dotnet` formula installs a newer major version, which cannot run `net9.0` apps on its own. If other tools can't find .NET, also set `export DOTNET_ROOT="/opt/homebrew/opt/dotnet@9/libexec"`.

`node` and `openjdk` are only needed to run [generate.sh](./generate.sh), as the openapi-generator-cli is a Node wrapper around a Java tool.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the values for `certPath` and `keyFile` in [Program.cs](./api-client/Program.cs) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
setup_local.sh
run_test.sh
```

## Code generation

The C# API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

The generation script takes the API version and the spec name as arguments, e.g. `./generate.sh 4.0.2 beef` (the defaults). The spec is downloaded from `https://docs.aiaplatform.com.au/api/<version>/<name>.json`, so `openapi` generates a client for every endpoint.

Some constructs in the API's OpenAPI spec are not handled correctly by the C# generator, so [generate.sh](./generate.sh) works around them:

- Before generating, the downloaded spec is adjusted: boolean `const` values, `pattern`s on date fields and "Empty object" `oneOf` branches are removed, discriminator properties lose their `const`, and multi-type values (such as `type: ["number", "string", "boolean"]`) are left untyped.
- A customised [JsonConverter.mustache](./templates/libraries/generichost/JsonConverter.mustache) template fixes serialisation of `oneOf` models and optional enum fields.
- **Temporary:** `gas` is made optional on `OutputMethod1`/`OutputMethod2`, because the API currently omits it from some outputs (such as `scope3.services`). This should be removed once the API or spec is fixed.
