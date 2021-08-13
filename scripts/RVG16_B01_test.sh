#!/bin/bash

SAVE_PATH="_test/"
BLOCK_NAME="RVG16_B01"

python -u generate_nwb.py $BLOCK_NAME --save_path $SAVE_PATH
