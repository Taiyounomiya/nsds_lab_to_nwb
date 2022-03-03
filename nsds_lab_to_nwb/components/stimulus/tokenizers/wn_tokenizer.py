import logging

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
        stim_dur = self.stim_configs['duration']
        bl_start = self.stim_configs['baseline_start']
        bl_end = self.stim_configs['baseline_end']
        if not (stim_dur < bl_start and bl_start < bl_end):
            raise ValueError('Baseline period should start after the stimulus.'
                             f'Got stim duration={stim_dur}, baseline_start={bl_start} '
                             f'and baseline_end={bl_end}, relative to stim onsets.')

        trial_list = []

        # period before the first stimulus starts
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b'))

        for i, onset in enumerate(stim_onsets):
            # actual stimulus (always starts at stim_onset)
            start_time = onset
            stop_time = onset + stim_dur
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='s'))

            # in-trial baseline period
            start_time = onset + bl_start
            stop_time = onset + bl_end
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
