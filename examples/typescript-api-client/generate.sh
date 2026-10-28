#!/bin/bash
set -e
API_CLIENT_DIR=api-client
API_VERSION=${1:-4.0.2}
SPEC_NAME=${2:-beef}
rm -rf $API_CLIENT_DIR

# SPEC_NAME is either the name of a published spec, or a path to a local spec file
if [[ -f "$SPEC_NAME" ]]; then
  SPEC_INPUT=$SPEC_NAME
else
  SPEC_INPUT=https://docs.aiaplatform.com.au/api/$API_VERSION/$SPEC_NAME.json
fi

npm -g install @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i $SPEC_INPUT \
  -g typescript-fetch \
  -t templates \
  -o $API_CLIENT_DIR \
  --global-property apiTests=false,apiDocs=false,modelTests=false,modelDocs=false
  
cp resources/* $API_CLIENT_DIR/

cd $API_CLIENT_DIR
./setup_local.sh
./run_test.sh