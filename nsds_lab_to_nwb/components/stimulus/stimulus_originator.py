import logging
import os

from nsds_lab_to_nwb.components.stimulus.mark_manager import MarkManager
from nsds_lab_to_nwb.components.stimulus.trials_manager import TrialsManager
from nsds_lab_to_nwb.components.stimulus.wav_manager import WavManager
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
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
        stim_name = self.stim_configs['name']
        _, stim_info = check_stimulus_name(stim_name)
        parameter_path = stim_info['parameter_path']
        if parameter_path is None or len(parameter_path) == 0:
            return None
        return os.path.join(self.stim_lib_path, parameter_path)

    def make(self, nwb_content):
        stim_name = self.stim_configs['name']
        stim_type = self.stim_configs['type']  # either 'discrete' or 'continuous'
        logger.info(f'Stimulus name: {stim_name} (type: {stim_type})')

        # add mark track
        logger.info('Adding marks...')
        mark_time_series, mark_events = self.mark_manager.get_mark_track()
        nwb_content.add_stimulus(mark_time_series)

        # tokenize into trials, based on the mark track
        logger.info('Tokenizing into trials...')
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate
        self.trials_manager.add_trials(nwb_content, mark_events, rec_end_time)

        # add stimulus WAV data
        logger.info('Adding stimulus waveform...')
        audio_start_time = self.trials_manager.get_audio_start_time()
        stim_wav_time_series = self.wav_manager.get_stim_wav(starting_time=audio_start_time)
        if stim_wav_time_series is not None:
            nwb_content.add_stimulus(stim_wav_time_series)
