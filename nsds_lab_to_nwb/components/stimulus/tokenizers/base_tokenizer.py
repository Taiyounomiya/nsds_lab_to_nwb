class BaseTokenizer():
    """ Base Tokenizer class for auditory stimulus data
    """
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.custom_columns = None

    def tokenize(self, mark_dset, stim_vals):
        stim_onsets = self._get_stim_onsets(mark_dset)
        rec_end_time = mark_dset.num_samples / mark_dset.rate
        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    stim_dur=self.stim_configs['duration'],
                                    bl_start=self.stim_configs['baseline_start'],
                                    bl_end=self.stim_configs['baseline_end'],
                                    rec_end_time=rec_end_time)
        return trial_list

    def _tokenize(self, mark_dset, rec_end_time):
        raise NotImplementedError

    def _get_stim_onsets(self, mark_dset):
        raise NotImplementedError

    def _get_mark_threshold(self, mark_dset):
        return mark_dset.data[:], self.stim_configs['mark_threshold']
