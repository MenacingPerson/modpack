#!/usr/bin/env bash

set -e

cd "$(realpath "$(dirname "$0")"/..)"

rm -f ./packs/*.mrpack

for i in $(jq -r '.build[]' < conf/base_config.json)
do
    if [[ -d ./conf/$i ]]
    then
        script -eq -c "./setup.py $i" /dev/null
    fi
done

./scripts/gen_mod_list.sh > mod-list.md
