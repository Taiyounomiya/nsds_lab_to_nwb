#!/bin/bash

# standard paths on catscan
export NSDS_METADATA_PATH='/clusterfs/NSDS_data/NSDSLab-NWB-metadata/'
export NSDS_DATA_PATH='/clusterfs/NSDS_data/raw/'
export NSDS_STIMULI_PATH='/clusterfs/NSDS_data/stimuli/'

SAVE_PATH="/clusterfs/NSDS_data/nwb/test/"

# all test blocks on catscan
BLOCK_LIST=("RVG16_B01"  # wn2
            "RVG16_B02"  # tone_diagnostic
            "RVG16_B03"  # wn2
            "RVG16_B04"  # tone_diagnostic
            "RVG16_B05"  # tone_diagnostic
            "RVG16_B06"  # tone
            "RVG16_B07"  # tone150
            "RVG16_B08"  # TIMIT, *bad block*
            "RVG16_B09"  # no stim, *bad block*
            "RVG16_B10"  # dmr
            "RVG21_B12"  # baseline stim
            "RVG21_B13"  # TIMIT
            "R56_B10"
            "R56_B13"
            )

for BLOCK_NAME in "${BLOCK_LIST[@]}"; do
    echo "~~~"
    echo "processing $BLOCK_NAME"
    python -u generate_nwb.py $BLOCK_NAME --save_path $SAVE_PATH
done
