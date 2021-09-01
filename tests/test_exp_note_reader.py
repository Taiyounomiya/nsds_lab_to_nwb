import os
import unittest

from nsds_lab_to_nwb.metadata.exp_note_reader import ExpNoteReader
from nsds_lab_to_nwb.utils import get_data_path, split_block_folder


class TestCase_ExpNoteReader(unittest.TestCase):

    data_path = get_data_path()
    write_path = '_test/'

    def test_ods_to_yaml(self):
        ''' read an RFLYY_Experiment_Notes.ods file,
        and write a RFLYY_BXX.yaml file.
        '''
        block_folder = 'RVG16_B02'
        _, animal_name, _ = split_block_folder(block_folder)
        experiment_path = os.path.join(self.data_path, animal_name)
        reader = ExpNoteReader(experiment_path, block_folder)
        reader.dump_yaml(write_path=self.write_path)


if __name__ == '__main__':
    unittest.main()
