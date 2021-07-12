class StimulusTokenizer():
    """ Base Tokenizer class for auditory stimulus data
    """
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.custom_columns = None

    def tokenize(self, nwb_content, stim_vals, mark_name='recorded_mark'):
        if self._already_tokenized(nwb_content):
            print('Block has already been tokenized')
            return
        self._add_trial_columns(nwb_content)
        mark_dset = self.read_mark(nwb_content, mark_name)
        rec_end_time = self._get_end_time(nwb_content, mark_name)
        trial_list = self._tokenize(stim_vals, mark_dset, rec_end_time)
        for trial_kwargs in trial_list:
            nwb_content.add_trial(**trial_kwargs)

    def _tokenize(self, mark_dset, rec_end_time):
        raise NotImplementedError('should be implemeted in inherited class')

    def _already_tokenized(self, nwb_content):
        if not nwb_content.trials:
            return False
        if self.custom_columns is None:
            return False
        has_custom_trial_columns = ((column_args[0] in nwb_content.trials.colnames)
                                    for column_args in self.custom_columns)
        return all(has_custom_trial_columns)

    def __get_stim_onsets(self, nwb_content, mark_name):
        raise NotImplementedError('should be implemeted in inherited class')

    def _add_trial_columns(self, nwb_content):
        if self.custom_columns is None:
            raise ValueError('self.custom_columns should be set for specific stimulus type.')
        for column_args in self.custom_columns:
            nwb_content.add_trial_column(*column_args)

    def _get_end_time(self, nwb_content, mark_name):
        mark_dset = self.read_mark(nwb_content, mark_name=mark_name)
        end_time = mark_dset.num_samples/mark_dset.rate
        return end_time

    def read_mark(self, nwb_content, mark_name='recorded_mark'):
        return nwb_content.stimulus[mark_name]

    def read_raw(self, nwb_content, device_name):
        """
        Read a raw dataset from the currently open nwb file
        """
        return nwb_content.acquisition[device_name]
