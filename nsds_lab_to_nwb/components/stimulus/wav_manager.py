import logging
import os
import numpy as np
from scipy.io import wavfile

from pynwb import TimeSeries

from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
from nsds_lab_to_nwb.utils import get_stim_lib_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WavManager():
    def __init__(self, stim_lib_path, stim_configs):
        self.stim_name = stim_configs['name']
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.stim_configs = stim_configs

    def get_stim_wav(self, starting_time, name='raw_stimulus'):
        if self.stim_name == 'wn1':
            return None

        stim_file = self.get_stim_file(self.stim_name, self.stim_lib_path)
        if stim_file is None:
            logger.info(f'Stimulus [{self.stim_name}] has no audio file. ' +
                        'No stimulus will be added to the NWB file.')
            return None

        logger.debug(f'Loading stimulus from: {stim_file}')
        return self._get_stim_wav(stim_file, starting_time, name=name)

    def _get_stim_wav(self, stim_file, starting_time, name='raw_stimulus'):
        ''' get the raw wav stimulus track '''
        # Read the stimulus wav file
        stim_wav_fs, stim_wav = wavfile.read(stim_file)
        rate = float(stim_wav_fs)

        # Create the stimulus timeseries
        stim_time_series = TimeSeries(name=name,
                                      data=stim_wav,
                                      starting_time=starting_time,
                                      unit='Volts',
                                      rate=rate,
                                      description='The neural recording aligned stimulus track.')
        return stim_time_series

    @staticmethod
    def get_stim_file(stim_name, stim_path):
        _, stim_info = check_stimulus_name(stim_name)
        if stim_info['audio_path'] is None:
            # when there is no associated audio file (e.g., baseline)
            return None
        return os.path.join(stim_path, stim_info['audio_path'])
