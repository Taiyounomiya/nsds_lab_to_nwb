from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class SingleTokenizer(BaseTokenizer):
    """
    Tokenize into a single stimulus trial, with possible baseline trials before/after.
    Suitable for DMR stimulus or baseline (no stimulus) blocks.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'SingleTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('stim_name', 'Stimulus name')]

    def _validate_num_stim_onsets(self, stim_onsets):
        # in the continuous case, we only look for the *first* stim onset.
        num_onsets = len(stim_onsets)
        mismatch_msg = (
            f"{self.tokenizer_type}: "
            + "No stimulus onsets found "
            + f"in block {self.block_name}. "
            + "Expected at least one.")

        if num_onsets == 0:
            raise ValueError(mismatch_msg)

    def _tokenize(self, stim_vals, stim_onsets,
                  *, rec_end_time, audio_start_time=None, audio_end_time=None):
        stim_name = self.stim_configs['name']
        if stim_name == 'baseline':
            # add single trial
            trial_list = [dict(start_time=0.0,
                               stop_time=rec_end_time,
                               sb='b',
                               stim_name=stim_name)]
            return trial_list

        # -- in case of continuous stimulus, such as DMR --
        stim_start_time = stim_onsets[0]

        trial_list = []

        # add pre-stimulus period to baseline
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_start_time,
                               sb='b',
                               stim_name=''))

        # add single trial with continuous stimulus
        trial_list.append(dict(start_time=stim_start_time,
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
