import os
import uuid

from pynwb import NWBFile
from nsds_lab_to_nwb.common.data_scanners import AuditoryDataScanner
from nsds_lab_to_nwb.common.time import get_default_time
from nsds_lab_to_nwb.components.stimulus.mark_manager import MarkManager
from nsds_lab_to_nwb.components.stimulus.trials_manager import TrialsManager
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager
from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder)

import pytest


data_path = get_data_path()
metadata_lib_path = get_metadata_lib_path()
stim_lib_path = get_stim_lib_path()


@pytest.mark.xfail
def test_wn_tokenizer(self):
    ''' test white noise stimulus tokenizer '''
    block_name = 'RVG16_B01'
    self.__run_test_tokenizer(block_name)


@pytest.mark.xfail
def test_tone_tokenizer(self):
    ''' test tone stimulus tokenizer '''
    block_name = 'RVG16_B06'
    self.__run_test_tokenizer(block_name)


@pytest.mark.xfail
def test_timit_tokenizer(self):
    ''' test TIMIT stimulus tokenizer '''
    block_name = 'RVG16_B08'
    self.__run_test_tokenizer(block_name)


def __run_test_tokenizer(self, block_name):
    _, animal_name, _ = split_block_folder(block_name)
    block_metadata_path = os.path.join(self.data_path, animal_name, block_name,
                                       f"{block_name}.yaml")
    metadata = MetadataManager(block_folder=block_name,
                               block_metadata_path=block_metadata_path,
                               metadata_lib_path=self.metadata_lib_path,
                               legacy_block=False).extract_metadata()
    stim_configs = metadata['stimulus']
    stim_vals = None
    # stim_vals = StimValueExtractor(stim_configs, self.stim_lib_path).extract()

    dataset = AuditoryDataScanner(block_name,
                                  data_path=self.data_path,
                                  stim_lib_path=self.stim_lib_path,
                                  use_htk=False).extract_dataset()

    # create an empty NWB file
    nwb_content = NWBFile(session_description='test stim tokenizers',  # required
                          identifier=str(uuid.uuid1()),  # required
                          session_start_time=get_default_time())  # required
    # add mark track
    mark_time_series = MarkManager(dataset).get_mark_track(starting_time=0.0)
    nwb_content.add_stimulus(mark_time_series)

    # tokenize and add trials
    trials_manager = TrialsManager(block_name, stim_configs)
    trials_manager.add_trials(nwb_content, stim_vals)
