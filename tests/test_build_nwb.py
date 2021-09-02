import os
import unittest

from nsds_lab_to_nwb.nwb_builder import NWBBuilder
from nsds_lab_to_nwb.utils import split_block_folder, get_data_path


class TestCase_Build_NWB(unittest.TestCase):

    data_path = get_data_path()
    metadata_save_path = '_test/'
    out_path = '_test/'

    def test_build_nwb_single_block(self):
        ''' build NWB but do not write file to disk '''
        block_folder = 'RVG16_B08'
        resample_data = False   # for testing
        # resample_data = True
        use_htk = False
        self.__build_nwb_content(block_folder, resample_data, use_htk)

    def __build_nwb_content(self, block_folder, resample_data=True, use_htk=False):
        ''' build NWB but do not write file to disk '''
        _, animal_name, _ = split_block_folder(block_folder)
        block_metadata_path = os.path.join(self.data_path, animal_name, block_folder,
                                           f"{block_folder}.yaml")
        nwb_builder = NWBBuilder(data_path=self.data_path,
                                 block_folder=block_folder,
                                 save_path=self.out_path,
                                 block_metadata_path=block_metadata_path,
                                 metadata_save_path=self.metadata_save_path,
                                 resample_data=resample_data,
                                 use_htk=use_htk)
        nwb_content = nwb_builder.build()
        assert nwb_content is not None


if __name__ == '__main__':
    unittest.main()
