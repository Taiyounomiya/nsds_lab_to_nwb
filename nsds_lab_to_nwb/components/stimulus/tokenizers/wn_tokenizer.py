import logging
import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class WNTokenizer(BaseTokenizer):
    """
    Tokenize into discrete white noise stimulus trials.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'WNTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, audio_start_time, audio_end_time, rec_end_time):
        bl_start = self.stim_configs['baseline_start']
        stim_dur = self.stim_configs['duration']
        bl_end = self.stim_configs['baseline_end']

        trial_list = []

        # period before the first stimulus starts
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b'))

        for i, onset in enumerate(stim_onsets):
            # in-trial, pre-signal baseline
            start_time = onset
            stop_time = start_time + bl_start
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b'))

            # actual signal
            start_time = stop_time
            stop_time = start_time + stim_dur
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='s'))

            # in-trial, post-signal baseline
            start_time = stop_time
            stop_time = start_time + bl_end
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b'))

        # period after the end of last stim trial until recording stops
        if stop_time < rec_end_time:
            start_time = stop_time
            trial_list.append(dict(start_time=start_time,
                                   stop_time=rec_end_time,
                                   sb='b'))

        return trial_list
