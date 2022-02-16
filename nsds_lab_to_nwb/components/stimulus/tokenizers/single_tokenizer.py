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

    def tokenize(self, mark_onsets, mark_time_series, stim_vals):
        stim_onsets = None  # not needed in this case
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate
        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    rec_end_time=rec_end_time)
        return trial_list

    def _tokenize(self, stim_vals, stim_onsets, *, rec_end_time, **unused_metadata):
        stim_name = self.stim_configs['name']
        if stim_name == 'baseline':
            sb = 'b'
        else:
            sb = 's'

        # add single trial
        trial_list = [dict(start_time=0.0,
                           stop_time=rec_end_time,
                           sb=sb,
                           stim_name=stim_name)]
        return trial_list
