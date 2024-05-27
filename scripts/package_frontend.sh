#!/bin/bash
set -xe

FILENAME=mulletwebhook-frontend.zip
VERSION="$1"
if [ -n ${VERSION} ]; then
    FILENAME="mulletwebhook-frontend-${VERSION}.zip"
fi

# packages frontend deps for upload

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

mkdir -p ${SCRIPTPATH}/../dist

cd ${SCRIPTPATH}/../frontend
zip -r ${SCRIPTPATH}/../dist/${FILENAME} .
cd -
