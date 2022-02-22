import logging
import numpy as np

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

    def tokenize(self, mark_events, mark_time_series, stim_vals):
        stim_onsets = self.get_stim_onsets(mark_events, mark_time_series)
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate

        stim_start_time = stim_onsets[0]
        audio_start_time = stim_start_time - self.stim_configs['first_mark']
        audio_end_time = audio_start_time + self.stim_configs['play_length']
        last_marker_time = stim_onsets[-1]

        stim_name = self.stim_configs['name']
        logger.debug(f'Tokenizing {stim_name} stimulus.')
        logger.debug(f'audio file start time: {audio_start_time}')
        logger.debug(f'stim onset: {stim_start_time}')
        logger.debug(f'last marker: {last_marker_time}')
        logger.debug(f'audio file end time: {audio_end_time} ')
        logger.debug(f'recording end time: {rec_end_time}')

        self._validate_num_stim_onsets(stim_vals, stim_onsets)

        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    audio_start_time=audio_start_time,
                                    audio_end_time=audio_end_time,
                                    rec_end_time=rec_end_time)
        return trial_list

    def _tokenize(self, stim_vals, stim_onsets, **kwargs):
        raise NotImplementedError

    def get_stim_onsets(self, mark_events, mark_time_series, use_tdt_mark_events=False):
        mark_offset = self.stim_configs['mark_offset']
        if use_tdt_mark_events and mark_events is not None:
            # loaded directly from TDT object
            # (now suppressed by use_tdt_mark_events=False because wn2 requires re-detection)
            logger.info('Using marker events directly loaded from TDT')
            logger.debug(f'found {len(mark_events)} onsets from TDT-detected events')
            return mark_events + mark_offset

        logger.info('Detecting stimulus onsets by thresholding the mark track')
        mark_rate = mark_time_series.rate
        stim_duration = self.stim_configs.get('duration', None)
        mark_threshold = self._get_mark_threshold()
        mark_events = self._get_mark_events(mark_time_series.data[:],
                                            mark_rate, mark_threshold,
                                            min_separation=stim_duration)
        logger.debug(f'found {len(mark_events)} onsets by thresholding mark track')
        return mark_events + mark_offset

    def _get_mark_events(self, mark_data, mark_rate, mark_threshold,
                         min_separation=None):
        mark_front_padded = np.concatenate((np.array([0.]), mark_data), axis=0)
        thresh_crossings = np.diff((mark_front_padded > mark_threshold).astype('int'),
                                   axis=0)
        mark_events_idx = np.where(thresh_crossings > 0.5)[0]
        mark_events = mark_events_idx / mark_rate

        if min_separation is not None:
            # if two adjacent marks are too close, drop the latter one
            too_close = np.where((mark_events[1:] - mark_events[:-1])
                                 < min_separation)[0] + 1
            mark_events = np.delete(mark_events, too_close)

        return mark_events

    def _get_mark_threshold(self):
        # NOTE: this is only used when TDT-loaded mark onsets are not available.
        # see issue #102 for more discussion on mark thresholds.
        mark_threshold = self.stim_configs['mark_threshold']
        logger.debug(f'using mark_threshold={mark_threshold} from metadata input')
        return mark_threshold

    def _validate_num_stim_onsets(self, stim_vals, stim_onsets):
        ''' Validate that the number of identified stim onsets
        is equal to the number of stim parameterizations in stim_vals.
        '''
        num_onsets = len(stim_onsets)
        num_expected_trials = len(stim_vals)
        mismatch_msg = (
            f"{self.tokenizer_type}: "
            + "Incorrect number of stimulus onsets found "
            + f"in block {self.block_name}. "
            + f"Expected {num_expected_trials}, found {num_onsets}.")

        if num_onsets != num_expected_trials:
            raise ValueError(mismatch_msg)
