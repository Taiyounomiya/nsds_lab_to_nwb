from nsds_lab_to_nwb.components.stimulus.wav_manager import WavManager
from nsds_lab_to_nwb.utils import get_stim_lib_path

import pytest


stim_name = 'White noise'
stim_path = get_stim_lib_path()
stim_metadata = {'name': stim_name,
                 'mark_offset': 0, 'first_mark': 0   # dummy values
                 }


@pytest.mark.xfail
def test_get_stim_files():
    ''' detect stimulus file path by the stimulus name '''
    # note: get_stim_file() is a staticmethod
    wm = WavManager(stim_path, stim_metadata)
    for st_name in ('White noise', 'wn2'):
        wm.get_stim_file(st_name, stim_path)


@pytest.mark.xfail
def test_get_stim_wav():
    ''' detect and load stimulus wav file by the stimulus name '''
    wm = WavManager(stim_path, stim_metadata)
    first_recorded_mark = 10.    # just a dummy number
    wm.get_stim_wav(first_recorded_mark)
