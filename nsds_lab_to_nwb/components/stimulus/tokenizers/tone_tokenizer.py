from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class ToneTokenizer(BaseTokenizer):
    """
    Tokenize into discrete tone pip stimulus trials.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'ToneTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('frq', 'Stimulus Frequency'),
                                     ('amp', 'Stimulus Amplitude')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, audio_start_time, audio_end_time, rec_end_time):
        bl_start = self.stim_configs['baseline_start']
        stim_dur = self.stim_configs['duration']
        bl_end = self.stim_configs['baseline_end']

        trial_list = []

        none_str = 'nan'    # for indicating baseline frq and amp

        # period before the first stimulus starts
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b',
                               frq=none_str,
                               amp=none_str))

        for i, onset in enumerate(stim_onsets):
            frq = str(stim_vals[i, 1])
            amp = str(stim_vals[i, 0])

            # in-trial, pre-signal baseline
            start_time = onset
            stop_time = start_time + bl_start
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

            # actual signal
            start_time = stop_time
            stop_time = start_time + stim_dur
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='s',
                                   frq=frq,
                                   amp=amp))

            # in-trial, post-signal baseline
            start_time = stop_time
            stop_time = start_time + bl_end
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

        # period after the end of last stim trial until recording stops
        if stop_time < rec_end_time:
            start_time = stop_time
            trial_list.append(dict(start_time=start_time,
                                   stop_time=rec_end_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

        return trial_list
