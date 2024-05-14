#!/bin/bash
set -xe

# packages frontend deps for upload

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

mkdir -p ${SCRIPTPATH}/../dist

cd ${SCRIPTPATH}/../frontend
zip -r ${SCRIPTPATH}/../dist/mulletwebhook-frontend.zip .
cd -
