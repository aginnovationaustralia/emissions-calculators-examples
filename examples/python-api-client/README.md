# Example Python API client for the AIA Carbon Calculators API

This example shows how to call the REST API available at https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0 using a simple Python script.

## Running the example

You can execute a simple request to the `beef` endpoint using the example provided. You just need to update the parameters `cert_file="cert.pem"` and `key_file="key.pem"` in [test_api.py](./api-client/test_api.py) so they point to your client certificate and key files. This allows the client to authenticate with the endpoint via mTLS. Once that has been done you just need to run:

```
cd api-client
setup_local.sh
run_test.sh
```

## Code generation

The Python API client has been generated using the [openapi-generator-cli](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) tool. The generation can be reproduced by running [generate.sh](./generate.sh). If you supply your mTLS certificate files correctly (you can place them in the resources folder and they will be copied in) the generation script should be able to execute the sample test successfully.

For now, the Python generator does not support all the configuration needed for an mTLS connection out of the box. Several fixes have been applied to the generated code in the `api-client` folder to let this work end to end, using [user defined templates](https://openapi-generator.tech/docs/customization#user-defined-templates). Once this [PR](https://github.com/OpenAPITools/openapi-generator/pull/22229) has been merged and released, it will be possible to make requests via mTLS without any code changes to the generated Python client code needed.
