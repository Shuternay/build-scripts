#!/bin/sh

for x in `find '../problems' -name 'pics' -type d`; do
    pushd "$x"
    for y in *.mp; do
        mpost "$y"
    done
    popd
done

for p in problems
do
    latex "$p.tex" || break
    latex "$p.tex" || break
    dvips -t a4 $p.dvi -o $p.ps
    dvipdfmx -p a4 $p.dvi
done
