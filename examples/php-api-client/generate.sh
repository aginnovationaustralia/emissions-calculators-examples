#!/bin/bash
set -e
API_CLIENT_DIR=api-client
API_VERSION=${1:-4.0.2}
SPEC_NAME=${2:-beef}
rm -rf $API_CLIENT_DIR

# Download the spec and adjust constructs the PHP generator handles badly. PHP flattens each
# oneOf into a single model, so:
# - a `const` on a oneOf variant becomes a single-value enum that rejects the other variants, so drop consts
# - likewise an `enum` on a oneOf variant's property only keeps one variant's values, so drop those enums
# - an "Empty object" oneOf branch adds nothing, so drop it
# - a `pattern` on a `format: date` field is checked against a DateTime, so drop it
SPEC_FILE=$(mktemp -d)/openapi.json
curl -sSf https://docs.aiaplatform.com.au/api/$API_VERSION/$SPEC_NAME.json -o $SPEC_FILE
node -e '
const fs = require("fs");
const file = process.argv[1];
const spec = JSON.parse(fs.readFileSync(file, "utf8"));
const isEmptyObject = (s) =>
  s && s.type === "object" && s.properties && Object.keys(s.properties).length === 0 && s.additionalProperties === false;
const schemas = spec.components?.schemas ?? {};
const resolve = (s) => (s && s.$ref ? schemas[s.$ref.split("/").pop()] : s);
const dropVariantEnums = (variants) => {
  for (const variant of variants.map(resolve)) {
    if (!variant) continue;
    for (const prop of Object.values(variant.properties ?? {})) delete prop.enum;
    if (Array.isArray(variant.oneOf)) dropVariantEnums(variant.oneOf);
  }
};
const walk = (o) => {
  if (Array.isArray(o)) return o.forEach(walk);
  if (o && typeof o === "object") {
    if ("const" in o && typeof o.const !== "object") delete o.const;
    if (o.format === "date" && "pattern" in o) delete o.pattern;
    if (Array.isArray(o.oneOf) && o.oneOf.some(isEmptyObject)) o.oneOf = o.oneOf.filter((s) => !isEmptyObject(s));
    if (Array.isArray(o.oneOf)) dropVariantEnums(o.oneOf);
    Object.values(o).forEach(walk);
  }
};
walk(spec);
fs.writeFileSync(file, JSON.stringify(spec));
' $SPEC_FILE

npm -g install @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g php \
  -o $API_CLIENT_DIR \
  --global-property apiTests=false,apiDocs=false,modelTests=false,modelDocs=false

cp resources/* $API_CLIENT_DIR/

cd $API_CLIENT_DIR
./setup_local.sh
./run_test.sh