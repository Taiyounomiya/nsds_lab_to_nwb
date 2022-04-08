import logging
import os

from pynwb import TimeSeries

from nsds_lab_to_nwb.components.stimulus.mark_manager import MarkManager
from nsds_lab_to_nwb.components.stimulus.trials_manager import TrialsManager
from nsds_lab_to_nwb.components.stimulus.wav_manager import WavManager
from nsds_lab_to_nwb.utils import get_stim_lib_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StimulusOriginator():
    def __init__(self, rec_manager, dataset, metadata):
        self.stim_lib_path = get_stim_lib_path(dataset.stim_lib_path)
        self.stim_configs = metadata['stimulus']

        self.mark_manager = MarkManager(rec_manager, self.stim_configs)
        self.wav_manager = WavManager(self.stim_lib_path,
                                      self.stim_configs)

        self.stim_configs['stim_params_path'] = self._get_stim_parameter_path()
        self.stim_configs['play_length'] = self.wav_manager.length

        self.trials_manager = TrialsManager(metadata['block_name'],
                                            self.stim_configs)

    def _get_stim_parameter_path(self):
        parameter_path = self.stim_configs['parameter_path']
        if parameter_path is None or len(parameter_path) == 0:
            return None
        return os.path.join(self.stim_lib_path, parameter_path)

    def make(self, nwb_content):
        stim_name = self.stim_configs['name']
        stim_type = self.stim_configs['type']  # either 'discrete' or 'continuous'
        logger.info(f'Stimulus name: {stim_name} (type: {stim_type})')

        # add recorded mark timeseries
        logger.info('Adding marks...')
        mark_start_time = 0.0    # start at rec start, because this is *recorded* mark
        mark_track, mark_rate, mark_events = self.mark_manager.get_mark_track()
        mark_time_series = TimeSeries(name='stim_onset_marks',  # previously 'recorded_mark'
                                      data=mark_track,
                                      unit='Volts',
                                      starting_time=mark_start_time,
                                      rate=mark_rate,
                                      description='Recorded mark that tracks stimulus onsets.')
        nwb_content.add_stimulus(mark_time_series)

        # tokenize into trials, based on the mark track
        logger.info('Tokenizing into trials...')
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate
        self.trials_manager.add_trials(nwb_content, mark_events, rec_end_time)

        # add auditory stimulus WAV data
        logger.info('Adding stimulus waveform...')
        audio_start_time = self.trials_manager.get_audio_start_time()  # audio played after rec start
        stim_wav, stim_rate = self.wav_manager.get_stim_wav()
        if stim_wav is not None:
            stim_time_series = TimeSeries(name='stim_waveform',  # previously 'raw_stimulus'
                                          data=stim_wav,
                                          starting_time=audio_start_time,
                                          unit='Volts',
                                          rate=stim_rate,
                                          description='Auditory stimulus waveform, aligned to neural recording.')
            nwb_content.add_stimulus(stim_time_series)
