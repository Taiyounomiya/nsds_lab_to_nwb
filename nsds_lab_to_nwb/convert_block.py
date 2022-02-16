import logging.config

from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path,
                                   get_stim_lib_path)
from nsds_lab_to_nwb.nwb_builder import NWBBuilder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def convert_block(block_folder: str,
                  save_path: str,
                  data_path=None,
                  stim_lib_path=None,
                  metadata_lib_path=None,
                  block_metadata_path=None,
                  metadata_save_path=None,
                  resample_data=True,
                  use_htk=False,
                  process_stim=True,
                  write_nwb=True,
                  return_nwb_path=False):
    '''Wrapper for converting a single block of data using NWBBuilder.
    '''
    logger.debug(f'Converting block {block_folder}')

    data_path = get_data_path(data_path)
    metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
    stim_lib_path = get_stim_lib_path(stim_lib_path)

    logger.debug(f'data_path={data_path}')
    logger.debug(f'metadata_lib_path={metadata_lib_path}')
    logger.debug(f'stim_lib_path={stim_lib_path}')
    logger.debug(f'save_path={save_path}')

    # create a builder for the block
    nwb_builder = NWBBuilder(block_folder=block_folder,
                             data_path=data_path,
                             save_path=save_path,
                             block_metadata_path=block_metadata_path,
                             metadata_save_path=metadata_save_path,
                             stim_lib_path=stim_lib_path,
                             resample_data=resample_data,
                             use_htk=use_htk)

    # build the NWB file content
    nwb_content = nwb_builder.build(process_stim=process_stim)

    # write to file
    if write_nwb:
        nwb_builder.write(nwb_content)
    else:
        logger.info('Finishing without writing to a file, because write_nwb is set to False.')

    if return_nwb_path:
        return nwb_builder.output_file
