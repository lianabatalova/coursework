#!/usr/bin/env bash

set -e
set -x

rm -rf ./package/build
mkdir -p ./package/build

for file in ./designer/*.ui;
do
    pyuic5 $file > ./package/build/"$(basename "$file" .ui).py"
done
