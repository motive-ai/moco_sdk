#!/bin/bash
if [ $# -lt 0 ]; then
    echo "Usage: $(basename $0) [MATLAB_BIN_DIR]"
    exit
fi
MOCO_PATH="${0%/*}"
if [ $# -gt 0 ]; then
 MEX=$1"/mex"
 MATLAB=$1"/matlab"
else
 MEX="mex"
 MATLAB="matlab"
fi

for f in $MOCO_PATH/src/*.c; do $MEX -I$MOCO_PATH/include/ -O CFLAGS="\$CFLAGS -std=c99" $f; done

rm moco_lib.slx
$MATLAB -nojvm -nosplash -nodesktop -r "run('$MOCO_PATH/make_moco_library.m'); exit();"