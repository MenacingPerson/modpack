#!/usr/bin/env bash

set -e

cd "$(realpath "$(dirname "$0")"/..)"

cd conf

for i in 1.*
do
    cd $i
    packwiz update --all
    packwiz refresh
    cd ..
done
