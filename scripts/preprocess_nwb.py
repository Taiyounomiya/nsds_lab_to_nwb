#!/user/bin/env python
import logging.config
import sys
import argparse
import glob
import os

from nsds_lab_to_nwb.preprocess_block import preprocess_block


if __name__ == '__main__':
    '''
    Copied and rearranged from process_nwb/scripts/preprocess_folder.py
    in [process_nwb](https://github.com/BouchardLab/process_nwb).
    '''
    parser = argparse.ArgumentParser(description='Preprocess a NWB file or all NWBs in a folder.' +
                                     '\nPerforms the following steps:' +
                                     '\n1) Resample to frequency and store result,' +
                                     '\n2) Remove 60Hz noise and remove and store the CAR, and' +
                                     '\n3) Perform and store a wavelet decomposition.')
    parser.add_argument('target_path', type=str, help='Target path, either a NWB file or a folder.')
    parser.add_argument('--initial_resample_rate', type=float, default=3200., help='Frequency to resample '
                        'to before performing wavelet transform.')
    parser.add_argument('--final_resample_rate', type=float, default=400., help='Frequency to resample '
                        'to after calculating wavelet amplitudes.')
    parser.add_argument('--filters', type=str, default='rat',
                        choices=['rat', 'human', 'changlab'],
                        help='Type of filter bank to use for wavelets.')
    parser.add_argument('--all_filters', action='store_true')
    parser.add_argument('--acq_name', type=str, default='ECoG',
                        help='Name of acquisition in NWB file')
    parser.add_argument('--display_log', action='store_true',
                        help='Dislay log to screen, instead of writing to a file.')

    args = parser.parse_args()

    target_path = args.target_path
    initial_resample_rate = args.initial_resample_rate
    final_resample_rate = args.final_resample_rate
    filters = args.filters
    hg_only = not args.all_filters
    acq_name = str(args.acq_name)

    # configure logging
    display_log = args.display_log
    if display_log:
        logging.basicConfig(stream=sys.stderr)
    else:
        with path(nsds_lab_to_nwb, 'logging.conf') as fname:
            logging.config.fileConfig(fname, disable_existing_loggers=False)

    if target_path.endswith == '.nwb':
        # raise Exception('Please specify the folder CONTAINING the NWB file, not the nwb file itself')
        files = [target_path, ]
    else:
        files = glob.glob(os.path.join(target_path, '*.nwb'))

    if len(files) == 0:
        raise Exception('No NWB files in target path or invalid path')

    for nwb_path in files:
        print('Processing {}'.format(nwb_path))
        preprocess_block(nwb_path,
                         acq_name=acq_name,
                         initial_resample_rate=initial_resample_rate,
                         final_resample_rate=final_resample_rate,
                         filters=filters,
                         hg_only=hg_only)
