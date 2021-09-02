import os
import unittest

from nsds_lab_to_nwb.common.io import read_yaml
from nsds_lab_to_nwb.components.stimulus.stim_value_extractor import StimValueExtractor
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
from nsds_lab_to_nwb.utils import get_stim_lib_path, get_metadata_lib_path


class TestCase_StimValueExtractor(unittest.TestCase):

    stim_lib_path = get_stim_lib_path()
    metadata_lib_path = get_metadata_lib_path()

    def __test_stim(self, stim_name_input):
        stim_name, stim_info = check_stimulus_name(stim_name_input)
        stim_yaml_path = os.path.join(self.metadata_lib_path, 'auditory', 'yaml',
                                      'stimulus', stim_name + '.yaml')
        stim_configs = read_yaml(stim_yaml_path)
        sve = StimValueExtractor(stim_configs, self.stim_lib_path)
        stim_values = sve.extract()
        return stim_values

    def test_white_noise_stimuli(self):
        stim_name = 'wn2'
        stim_values = self.__test_stim(stim_name)
        assert stim_values is not None

    def test_tone_stimuli(self):
        stim_name = 'tone'
        stim_values = self.__test_stim(stim_name)
        assert stim_values is not None

        stim_name = 'tone150'
        stim_values = self.__test_stim(stim_name)
        assert stim_values is not None

    def test_timit_stimuli(self):
        stim_name = 'timit'
        stim_values = self.__test_stim(stim_name)
        assert stim_values is not None

    def test_dmr_stimuli(self):
        stim_name = 'dmr'
        stim_values = self.__test_stim(stim_name)
        assert stim_values is None


if __name__ == '__main__':
    unittest.main()
