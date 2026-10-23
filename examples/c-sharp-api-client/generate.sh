#!/bin/bash
set -e
API_CLIENT_DIR=api-client
API_VERSION=${1:-4.0.2}
rm -rf $API_CLIENT_DIR

# Download the spec and adjust constructs the C# generator emits broken code for:
# - a boolean `const` becomes an enum that does not compile, so drop `const` from boolean schemas
# - a `pattern` on a `format: date` field becomes a regex check on a DateOnly, so drop it
#   (the date format already constrains the value)
# - an "Empty object" oneOf branch matches any input, hiding the real value, so drop it
# - a discriminator property only accepts the last variant's `const`, so drop those consts
# - a multi-type value such as `type: ["number", "string", "boolean"]` becomes an object wrapper
#   that cannot read a primitive, so leave it untyped
SPEC_FILE=$(mktemp -d)/openapi.json
curl -sSf https://docs.aiaplatform.com.au/api/$API_VERSION/openapi.json -o $SPEC_FILE
node -e '
const fs = require("fs");
const file = process.argv[1];
const spec = JSON.parse(fs.readFileSync(file, "utf8"));
const schemas = spec.components?.schemas ?? {};
const isEmptyObject = (s) =>
  s && s.type === "object" && s.properties && Object.keys(s.properties).length === 0 && s.additionalProperties === false;
const resolve = (s) => (s && s.$ref ? schemas[s.$ref.split("/").pop()] : s);
const walk = (o) => {
  if (Array.isArray(o)) return o.forEach(walk);
  if (o && typeof o === "object") {
    if (o.type === "boolean" && "const" in o) delete o.const;
    if (o.format === "date" && "pattern" in o) delete o.pattern;
    if (Array.isArray(o.type) && o.type.length > 1) delete o.type;
    if (Array.isArray(o.oneOf) && o.oneOf.some(isEmptyObject)) o.oneOf = o.oneOf.filter((s) => !isEmptyObject(s));
    if (o.discriminator && Array.isArray(o.oneOf)) {
      for (const variant of o.oneOf.map(resolve)) {
        const prop = variant?.properties?.[o.discriminator.propertyName];
        if (prop && "const" in prop) delete prop.const;
      }
    }
    Object.values(o).forEach(walk);
  }
};
walk(spec);
// TEMPORARY: the API omits `gas` from some outputs (e.g. scope3.services, scope3.fuel) although
// the spec marks it required, which fails response parsing. Remove once the API or spec is fixed.
for (const name of ["OutputMethod1", "OutputMethod2"]) {
  const s = spec.components?.schemas?.[name];
  if (s?.required) s.required = s.required.filter((r) => r !== "gas");
}
fs.writeFileSync(file, JSON.stringify(spec));
' $SPEC_FILE

npm -g install @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g csharp \
  -t templates \
  -o $API_CLIENT_DIR \
  --global-property apiTests=false,apiDocs=false,modelTests=false,modelDocs=false \
  --library=generichost \
  --additional-properties targetFramework=net9.0
  
cp resources/* $API_CLIENT_DIR/

cd $API_CLIENT_DIR
./setup_local.sh
./run_test.sh
