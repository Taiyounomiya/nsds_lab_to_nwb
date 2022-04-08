from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager
from nsds_lab_to_nwb.utils import get_metadata_lib_path

import pytest


metadata_lib_path = get_metadata_lib_path()
metadata_save_path = '_test/'

@pytest.mark.xfail
def test_metadata_manager_case1_old_data():
    ''' detect/collect metadata needed to build the NWB file '''
    block_name = 'R56_B13'
    block_metadata_path = '_data/R56/R56_B13.yaml'
    nwb_metadata = MetadataManager(block_folder=block_name,
                                   block_metadata_path=block_metadata_path,
                                   metadata_lib_path=metadata_lib_path,
                                   metadata_save_path=metadata_save_path)
    nwb_metadata.extract_metadata()

@pytest.mark.xfail
def test_metadata_manager_case2_new_data():
    ''' detect/collect metadata needed to build the NWB file '''
    block_name = 'RVG16_B01'
    block_metadata_path = '_data/RVG16/RVG16_B01.yaml'
    nwb_metadata = MetadataManager(block_folder=block_name,
                                   block_metadata_path=block_metadata_path,
                                   metadata_lib_path=metadata_lib_path,
                                   metadata_save_path=metadata_save_path,
                                   legacy_block=False)
    nwb_metadata.extract_metadata()
