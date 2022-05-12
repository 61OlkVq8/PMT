#!/bin/bash

[ "$(docker images --filter=reference=slowcoach:latest)" = "" ] && { echo "No image tagged 'slowcoach:latest' found. Exiting."; exit 1; }

topDir=$(git rev-parse --show-toplevel)
buildDir=${topDir}/build

if [ $# -eq 1 ]; then set buildDir=$1; fi

if [ -f ${buildDir} ]; then echo "Provided build directory ${buildDir} is a file!" 1>&2; exit 1;
elif [ ! -d ${buildDir} ]; then mkdir -p ${buildDir};
fi

docker run --rm -it \
       -u $(id -u):$(id -g) \
       -v ${topDir}:/home/$USER/slowcoach \
       slowcoach:latest
