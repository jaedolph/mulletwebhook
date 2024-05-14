#!/bin/bash
set -xe

# downloads frontend dependancies

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

mkdir -p ${SCRIPTPATH}/../frontend/deps

curl https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js -L -o ${SCRIPTPATH}/../frontend/deps/Sortable.min.js
curl https://unpkg.com/htmx.org@1.9.12 -L -o ${SCRIPTPATH}/../frontend/deps/htmx.min.js

echo "ca68430703c4f5960e90735867c6e94d29b5a3de37107d8100e5a301007e9e6e ${SCRIPTPATH}/../frontend/deps/Sortable.min.js" | sha256sum -c
echo "449317ade7881e949510db614991e195c3a099c4c791c24dacec55f9f4a2a452 ${SCRIPTPATH}/../frontend/deps/htmx.min.js" | sha256sum -c
