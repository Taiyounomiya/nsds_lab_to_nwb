#!/bin/bash

SAVE_PATH="_test/"
BLOCK_NAME="R56_B13"
BLOCK_META="${NSDS_METADATA_PATH}/auditory/yaml/block/R56/R56_B13.yaml"

python -u generate_nwb.py $BLOCK_NAME --save_path $SAVE_PATH --block_metadata_path $BLOCK_META
