# Example C# API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0 using a simple C# script.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the values for `certPath` and `keyFile` in [Program.cs](./api-client/Program.cs) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
setup_local.sh
run_test.sh
```

## Code generation

The C# API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

For now, the C# code generation has some issues with optional enum fields. This may require patching manually if you are seeing problems with optional fields failing to serialise to JSON.