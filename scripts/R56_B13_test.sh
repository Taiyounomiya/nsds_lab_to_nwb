#!/bin/bash

SAVE_PATH="_test/"
BLOCK_NAME="R56_B13"
BLOCK_META="${NSDS_METADATA_PATH}/auditory/yaml/block/R56/R56_B13.yaml"

python generate_nwb.py  $SAVE_PATH $BLOCK_NAME --block_metadata_path $BLOCK_META
