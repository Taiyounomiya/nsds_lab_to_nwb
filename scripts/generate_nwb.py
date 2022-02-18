#!/user/bin/env python
import logging.config
import sys
import argparse
from importlib.resources import path

import nsds_lab_to_nwb
from nsds_lab_to_nwb.utils import str2bool
from nsds_lab_to_nwb.convert_block import convert_block


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert to a NWB file.')
    parser.add_argument('block_folder', type=str, help='<animal>_<block> block specification.')
    parser.add_argument('--save_path', '-o', type=str, default=None,
                        help='Path to save the NWB file.')
    parser.add_argument('--block_metadata_path', '-m', type=str, default=None,
                        help='Path to block metadata file.')
    parser.add_argument('--metadata_save_path', type=str, default=None,
                        help='Path to save intermediate metadata content.')
    parser.add_argument('--data_path', '-d', type=str, default=None,
                        help='Path to the top level data folder.')
    parser.add_argument('--metadata_lib_path', '-l', type=str, default=None,
                        help='Path to the metadata library repo.')
    parser.add_argument('--stim_lib_path', '-s', type=str, default=None,
                        help='Path to the stimulus library.')
    parser.add_argument('--use_htk', '-k', action='store_true',
                        help='Use data from HTK rather than TDT files.')
    parser.add_argument('--resample_data', '-r', type=str2bool, default=False,
                        help='Resample data to the nearest kHz.')
    parser.add_argument('--write_nwb', '-w', type=str2bool, default=True,
                        help='Write the NWB content to file.')
    parser.add_argument('--preprocess', '-p', type=str2bool, default=False,
                        help='Preprocess data and add a ProcessingModule to NWB.')
    parser.add_argument('--display_log', action='store_true',
                        help='Dislay log to screen, instead of writing to a file.')
    parser.add_argument('--test_run', action='store_true',
                        help='Force select arguments for testing.')

    args = parser.parse_args()
    save_path = args.save_path
    block_folder = args.block_folder

    # if None, will be replaced with standard paths downstream
    block_metadata_path = args.block_metadata_path
    data_path = args.data_path
    metadata_lib_path = args.metadata_lib_path
    stim_lib_path = args.stim_lib_path
    metadata_save_path = args.metadata_save_path

    # switches for processing
    use_htk = args.use_htk
    resample_data = args.resample_data
    write_nwb = args.write_nwb
    add_preprocessing = args.preprocess

    # switches for testing interface
    display_log = args.display_log
    if args.test_run:
        resample_data = False
        write_nwb = False
        display_log = True

    # configure logging
    if display_log:
        logging.basicConfig(stream=sys.stderr)
    else:
        with path(nsds_lab_to_nwb, 'logging.conf') as fname:
            logging.config.fileConfig(fname, disable_existing_loggers=False)

    # allow unspecified save_path when write_nwb is False
    if save_path is None:
        if write_nwb:
            raise ValueError('save_path is required for writing the NWB file.')
        else:
            save_path = '_test/'

    convert_block(block_folder=block_folder,
                  save_path=save_path,
                  data_path=data_path,
                  stim_lib_path=stim_lib_path,
                  metadata_lib_path=metadata_lib_path,
                  block_metadata_path=block_metadata_path,
                  metadata_save_path=metadata_save_path,
                  use_htk=use_htk,
                  resample_data=resample_data,
                  write_nwb=write_nwb,
                  add_preprocessing=add_preprocessing)
