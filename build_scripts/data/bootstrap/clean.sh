#!/bin/sh

for x in `find '../problems' -name 'pics' -type d`; do
    pushd "$x"
    for y in *.{1,log}; do
        [ -f "$y" ] || continue
        rm -v "$y"
    done
    popd
done

for x in *.{log,aux,dvi,ps,pdf}; do
    [ -f "$x" ] || continue
    rm -v "$x"
done
