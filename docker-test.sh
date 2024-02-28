#!/usr/bin/env bash

set -ex

ref="$(git log -1 --format=%h)"
img=tiledb-soma-$ref
# Invert exit code; `git bisect` assumes newer = broken, older = working, but in this case it's the opposite: build
# works on recent commits, we're looking for most recent broken commit.
! docker build -t $img --build-arg ref=$ref .
