import logging
import os
from scipy.io import wavfile

from pynwb import TimeSeries

from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
from nsds_lab_to_nwb.utils import get_stim_lib_path

logger = logging.getLogger(__name__)


class WavManager():
    def __init__(self, stim_lib_path, stim_configs):
        self.stim_name = stim_configs['name']
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.stim_configs = stim_configs

        self.stim_file = self.get_stim_file(self.stim_name, self.stim_lib_path)
        if self.stim_file is not None:
            self.stim_wav, self.rate, self.length = self.load_stim_from_wav_file()

        self.stim_wav_obj_name = 'stim_waveform'  # 'raw_stimulus' (previous name)

    def get_stim_wav(self, starting_time):
        if self.stim_file is None:
            logger.info(f'Stimulus [{self.stim_name}] has no audio file. ' +
                        'No stimulus will be added to the NWB file.')
            return None

        # Create the stimulus timeseries
        stim_time_series = TimeSeries(name=self.stim_wav_obj_name,
                                      data=self.stim_wav,
                                      starting_time=starting_time,
                                      unit='Volts',
                                      rate=self.rate,
                                      description='Auditory stimulus waveform, aligned to neural recording.')
        return stim_time_series

    def load_stim_from_wav_file(self):
        # Read the stimulus wav file
        logger.debug(f'Loading stimulus from: {self.stim_file}')
        stim_wav_fs, stim_wav = wavfile.read(self.stim_file)
        rate = float(stim_wav_fs)
        length = stim_wav.shape[0] / rate
        return stim_wav, rate, length

    @staticmethod
    def get_stim_file(stim_name, stim_path):
        _, stim_info = check_stimulus_name(stim_name)
        if stim_info['audio_path'] is None:
            # when there is no associated audio file (e.g., baseline)
            return None
        return os.path.join(stim_path, stim_info['audio_path'])
