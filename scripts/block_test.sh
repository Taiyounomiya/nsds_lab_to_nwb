#!/bin/bash
# -----------------------------------------------------------------
# Simplest use case: just specify the block name.
# ./block_test RVG16_B01
#
# To pass extra arguments, for example write_nwb=False:
# ./block_test RVG16_B01 --write_nwb False
#
# To turn on resample_data:
# ./block_test RVG16_B01 --resample_data True
#
# For a quick test run with both write_nwb and resample_data set to False:
# ./block_test RVG16_B01 --test_run
#
# See generate_nwb.py to learn about more input arguments options.
# -----------------------------------------------------------------

BLOCK_NAME=$1
TMP_PATH="_test/"

shift 1
EXTRA_ARGS=$@

python -u generate_nwb.py $BLOCK_NAME --save_path $TMP_PATH --metadata_save_path $TMP_PATH --display_log $EXTRA_ARGS
