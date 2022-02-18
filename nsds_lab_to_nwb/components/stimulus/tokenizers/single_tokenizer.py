from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class SingleTokenizer(BaseTokenizer):
    """
    Tokenize into a single trial, for stimulus data of type 'continuous'.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'SingleTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('stim_name', 'Stimulus name')]

    def tokenize(self, mark_events, mark_time_series, stim_vals,
                 audio_play_length):
        # in the continuous case, just looking for the *first* stim onset
        stim_onsets = self.get_stim_onsets(mark_events, mark_time_series)
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate
        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    rec_end_time=rec_end_time,
                                    audio_play_length=audio_play_length)
        return trial_list

    def _tokenize(self, stim_vals, stim_onsets,
                  *, audio_play_length, rec_end_time, **unused_metadata):
        stim_name = self.stim_configs['name']
        if stim_name == 'baseline':
            # add single trial
            trial_list = [dict(start_time=0.0,
                               stop_time=rec_end_time,
                               sb='b',
                               stim_name=stim_name)]
            return trial_list

        # -- in case of continuous stimulus, such as DMR --

        first_mark = self.stim_configs['first_mark']
        audio_start_time = stim_onsets[0] - first_mark
        audio_end_time = audio_start_time + audio_play_length

        trial_list = []

        # add pre-stimulus period to baseline
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b',
                               stim_name=''))

        # add single trial with continuous stimulus
        trial_list.append(dict(start_time=stim_onsets[0],
                               stop_time=min(audio_end_time, rec_end_time),
                               sb='s',
                               stim_name=stim_name))

        # add post-stimulus period to baseline
        if audio_end_time < rec_end_time:
            trial_list.append(dict(start_time=audio_end_time,
                                   stop_time=rec_end_time,
                                   sb='b',
                                   stim_name=''))
        return trial_list
