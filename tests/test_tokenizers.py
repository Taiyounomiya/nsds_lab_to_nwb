import unittest
import os

from pynwb import NWBFile
from nsds_lab_to_nwb.common.data_scanners import AuditoryDataScanner
from nsds_lab_to_nwb.common.time import get_default_time
from nsds_lab_to_nwb.components.stimulus.stimulus_originator import StimulusOriginator
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager
from nsds_lab_to_nwb.components.stimulus.tokenizers.tone_tokenizer import ToneTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.timit_tokenizer import TIMITTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.wn_tokenizer import WNTokenizer
from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder)


class TestCase_Tokenizers(unittest.TestCase):

    data_path = get_data_path()
    metadata_lib_path = get_metadata_lib_path()
    stim_lib_path = get_stim_lib_path()

    def test_wn_tokenizer(self):
        ''' test white noise stimulus tokenizer '''
        block_name = 'RVG16_B01'
        self.__run_test_tokenizer(block_name)

    def test_tone_tokenizer(self):
        ''' test tone stimulus tokenizer '''
        block_name = 'RVG16_B06'
        self.__run_test_tokenizer(block_name)

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

        dataset = AuditoryDataScanner(block_name,
                                      data_path=self.data_path,
                                      stim_lib_path=self.stim_lib_path,
                                      use_htk=False).extract_dataset()

        # choose tokenizer
        stim_name = stim_configs['name']
        if 'tone' in stim_name:
            tokenizer = ToneTokenizer(block_name, stim_configs)
        elif 'timit' in stim_name:
            tokenizer = TIMITTokenizer(block_name, stim_configs)
        elif 'wn' in stim_name:
            tokenizer = WNTokenizer(block_name, stim_configs)
        else:
            raise ValueError(f"Unknown stimulus type '{stim_name}' for mark tokenizer")

        # create an empty NWB file
        nwb_content = NWBFile(session_description='test stim tokenizers',  # required
                              identifier='NWB000',  # required
                              session_start_time=get_default_time())  # required
        # add stimulus
        stimulus_originator = StimulusOriginator(dataset, metadata)
        stimulus_originator.make(nwb_content)

        # tokenize
        tokenizer.tokenize(nwb_content)


if __name__ == '__main__':
    unittest.main()
