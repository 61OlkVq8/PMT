#!/bin/bash

# go to top level of working tree
cd $(git rev-parse --show-toplevel)
[ -f docker/Dockerfile ] || { echo "No Dockerfile found under docker directory. Please check if your repo structure is intact."; exit 1; }

export DOCKER_BUILDKIT=1
docker build -t 'slowcoach:latest' \
    --progress=plain \
    --build-arg USER=$(whoami) \
    --build-arg UID=$(id -u) \
    --build-arg GROUPS=$(id -g) \
    --build-arg HOME=${HOME} \
    - <docker/Dockerfile
