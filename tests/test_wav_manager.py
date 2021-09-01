import unittest

from nsds_lab_to_nwb.components.stimulus.wav_manager import WavManager
from nsds_lab_to_nwb.utils import get_stim_lib_path


class TestCase_WavManager(unittest.TestCase):

    stim_name = 'White noise'
    stim_path = get_stim_lib_path()
    stim_metadata = {'name': stim_name,
                     'mark_offset': 0, 'first_mark': 0   # dummy values
                     }

    wm = WavManager(stim_path, stim_metadata)

    def test_get_stim_files(self):
        ''' detect stimulus file path by the stimulus name '''
        # note: get_stim_file() is a staticmethod
        for st_name in ('White noise', 'wn2'):
            print(f'  detecting stimulus {st_name}...')
            self.wm.get_stim_file(st_name, self.stim_path)

    def test_get_stim_wav(self):
        ''' detect and load stimulus wav file by the stimulus name '''
        first_recorded_mark = 10.    # just a dummy number
        self.wm.get_stim_wav(first_recorded_mark)


if __name__ == '__main__':
    unittest.main()
