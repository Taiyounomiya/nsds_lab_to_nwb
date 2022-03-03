import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseTokenizer():
    """ Base Tokenizer class for auditory stimulus data
    """
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.tokenizer_type = 'BaseTokenizer'
        self.custom_trial_columns = None
        self.audio_start_time = None

    def tokenize(self, mark_events, rec_end_time):

        if self.stim_configs['name'] == 'baseline':
            # using SingleTokenizer._tokenize
            trial_list = self._tokenize(None, None, rec_end_time=rec_end_time)
            return trial_list

        mark_offset = self.stim_configs['mark_offset']      # from mark to actual stim onset
        stim_onsets = mark_events + mark_offset

        stim_start_time = stim_onsets[0]
        audio_start_time = mark_events[0] - self.stim_configs['first_mark']
        audio_end_time = audio_start_time + self.stim_configs['play_length']
        last_marker_time = mark_events[-1]

        stim_name = self.stim_configs['name']
        logger.debug(f'Tokenizing {stim_name} stimulus.')
        logger.debug(f'audio file start time: {audio_start_time}')
        logger.debug(f'stim onset: {stim_start_time}')
        logger.debug(f'last marker: {last_marker_time}')
        logger.debug(f'audio file end time: {audio_end_time} ')
        logger.debug(f'recording end time: {rec_end_time}')

        self._validate_num_stim_onsets(stim_onsets)
        self.audio_start_time = audio_start_time

        stim_vals = self._load_stim_parameters()
        if stim_vals is not None:
            if len(stim_vals) != self.stim_configs['nsamples']:
                raise ValueError('incorrect number of stimulus parameter sets found.')

        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    audio_start_time=audio_start_time,
                                    audio_end_time=audio_end_time,
                                    rec_end_time=rec_end_time)
        return trial_list

    def _load_stim_parameters(self):
        # override in Tone and TIMIT tokenizers
        return None

    def _tokenize(self, stim_vals, stim_onsets, **kwargs):
        raise NotImplementedError

    def _validate_num_stim_onsets(self, stim_onsets):
        ''' Validate that the number of identified stim onsets
        is equal to the known number of stimulus trials.
        '''
        num_onsets = len(stim_onsets)
        num_expected_trials = self.stim_configs['nsamples']
        mismatch_msg = (
            f"{self.tokenizer_type}: "
            + "Incorrect number of stimulus onsets found "
            + f"in block {self.block_name}. "
            + f"Expected {num_expected_trials}, found {num_onsets}.")

        if num_onsets != num_expected_trials:
            raise ValueError(mismatch_msg)
