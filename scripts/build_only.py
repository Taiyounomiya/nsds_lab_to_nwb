#!/user/bin/env python
import logging.config
import os
import sys
import argparse

from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path,
                                   get_stim_lib_path, split_block_folder)
from nsds_lab_to_nwb.nwb_builder import NWBBuilder

# display log to screen
logging.basicConfig(stream=sys.stderr)


def build_nwb(block_folder,
              save_path='_test/',
              block_metadata_path=None,
              metadata_save_path='_test/',
              resample_data=False,
              use_htk=False):
    ''' Build NWB content on catscan, but do not write file to disk.
    Use standard paths. Skip resampling. Intended for testing.
    '''
    # use standard paths
    data_path = get_data_path()
    stim_lib_path = get_stim_lib_path()

    # assume that metadata yaml file is stored with the data block
    if block_metadata_path is None:
        _, animal_name, _ = split_block_folder(block_folder)
        block_metadata_path = os.path.join(data_path, animal_name, block_folder,
                                           f"{block_folder}.yaml")
    nwb_builder = NWBBuilder(data_path=data_path,
                             block_folder=block_folder,
                             save_path=save_path,
                             block_metadata_path=block_metadata_path,
                             metadata_save_path=metadata_save_path,
                             stim_lib_path=stim_lib_path,
                             resample_data=resample_data,
                             use_htk=use_htk)
    nwb_content = nwb_builder.build()


if __name__ == '__main__':
    # just take a single string argument (the block name 'RFLYY_BXX')
    parser = argparse.ArgumentParser(description='NWB build test.')
    parser.add_argument('block_folder', type=str, help='<animal>_<block>')

    args = parser.parse_args()
    block_folder = args.block_folder

    build_nwb(block_folder)
