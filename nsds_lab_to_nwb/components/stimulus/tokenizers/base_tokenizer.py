import numpy as np


class BaseTokenizer():
    """ Base Tokenizer class for auditory stimulus data
    """
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.tokenizer_type = 'BaseTokenizer'
        self.custom_columns = None

    def tokenize(self, mark_dset, stim_vals):
        stim_onsets = self._get_stim_onsets(mark_dset)
        self._validate_num_stim_onsets(stim_vals, stim_onsets)
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
        mark_fs = mark_dset.rate
        mark_offset = self.stim_configs['mark_offset']

        mark_trk = mark_dset.data[:]
        mark_threshold = self.stim_configs['mark_threshold']
        thresh_crossings = np.diff((mark_trk > mark_threshold).astype('int'),
                                   axis=0)
        # adding +1 because diff gets rid of the 1st datapoint
        stim_onsets_idx = np.where(thresh_crossings > 0.5)[0] + 1

        stim_onsets = (stim_onsets_idx / mark_fs) + mark_offset
        return stim_onsets

    def _validate_num_stim_onsets(self, stim_vals, stim_onsets):
        ''' Validate that the number of identified stim onsets
        is equal to the number of stim parameterizations in stim_vals.
        '''
        num_onsets = len(stim_onsets)
        num_expected_trials = len(stim_vals)
        assert num_onsets==num_expected_trials, (
            f"{self.tokenizer_type}: "
            + "Incorrect number of stimulus onsets found "
            + f"in block {self.block_name}. "
            + f"Expected {num_expected_trials}, found {num_onsets}.")
