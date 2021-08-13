#!/bin/bash

SAVE_PATH="_test/"
BLOCK_NAME="R56_B13"

python -u generate_nwb.py $BLOCK_NAME --save_path $SAVE_PATH
