#!/bin/bash
set -e
API_CLIENT_DIR=api-client
API_VERSION=${1:-4.0.2}
SPEC_NAME=${2:-beef}
rm -rf $API_CLIENT_DIR

# Download the spec and drop "Empty object" oneOf branches: the generator maps them to `object`,
# and a PHP union type such as `object|SomeModel` is a compile error.
SPEC_FILE=$(mktemp -d)/openapi.json
curl -sSf https://docs.aiaplatform.com.au/api/$API_VERSION/$SPEC_NAME.json -o $SPEC_FILE
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
fs.writeFileSync(file, JSON.stringify(spec));
' $SPEC_FILE

npm -g install @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g php-nextgen \
  -o $API_CLIENT_DIR \
  --global-property apiTests=false,apiDocs=false,modelTests=false,modelDocs=false

cp resources/* $API_CLIENT_DIR/

cd $API_CLIENT_DIR
./setup_local.sh
./run_test.sh