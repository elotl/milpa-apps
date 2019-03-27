#!/bin/bash

set -e

if [[ $# -lt 1 ]]; then
    echo "usage: curl-servers.sh <load_balancer_address>"
    exit 1
fi

while /bin/true; do
    echo $1
    curl --max-time 2 -s $1 > /dev/null
    sleep 1
done
