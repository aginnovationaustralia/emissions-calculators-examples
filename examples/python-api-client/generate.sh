#!/bin/bash
set -e
API_CLIENT_DIR=api-client
API_VERSION=${1:-4.0.2}
SPEC_NAME=${2:-beef}
rm -rf $API_CLIENT_DIR

# Download the spec (or copy it, when SPEC_NAME is a path to a local file) and drop "Empty object"
# oneOf branches: the Python generator maps them to a plain object that matches any input, so every
# value would match more than one oneOf branch.
SPEC_FILE=$(mktemp -d)/openapi.json
if [[ -f "$SPEC_NAME" ]]; then
  cp "$SPEC_NAME" $SPEC_FILE
else
  curl -sSf https://docs.aiaplatform.com.au/api/$API_VERSION/$SPEC_NAME.json -o $SPEC_FILE
fi
node -e '
const fs = require("fs");
const file = process.argv[1];
const spec = JSON.parse(fs.readFileSync(file, "utf8"));
const isEmptyObject = (s) =>
  s && s.type === "object" && s.properties && Object.keys(s.properties).length === 0 && s.additionalProperties === false;
const walk = (o) => {
  if (Array.isArray(o)) return o.forEach(walk);
  if (o && typeof o === "object") {
    if (Array.isArray(o.oneOf) && o.oneOf.some(isEmptyObject)) o.oneOf = o.oneOf.filter((s) => !isEmptyObject(s));
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

# RESOLVE_INLINE_ENUMS turns any enum defined inline on a property into its own Python Enum class,
# rather than a plain string checked by a validator.
npm -g install @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g python \
  -o $API_CLIENT_DIR \
  --global-property apiTests=false,apiDocs=false,modelTests=false,modelDocs=false \
  --inline-schema-options RESOLVE_INLINE_ENUMS=true
  
cp resources/* $API_CLIENT_DIR/

cd $API_CLIENT_DIR
./setup_local.sh
./run_test.sh