#!/bin/bash

if [[ $# -lt 1 ]]; then
    echo "usage: curl-servers.sh <load_balancer_address>"
    exit 1
fi

while /bin/true; do
    curl --max-time 2 $1
    sleep 3
done
