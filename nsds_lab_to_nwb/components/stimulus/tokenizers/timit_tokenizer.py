from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class TIMITTokenizer(BaseTokenizer):
    """
    Tokenize TIMIT stimulus data

    Original version author: Max Dougherty <maxdougherty@lbl.gov>
    As part of MARS
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'TIMITTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('sample_filename', 'Sample Filename')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, stim_dur, bl_start, bl_end, rec_end_time):
        trial_list = []

        # Add the pre-stimulus period to baseline
        trial_list.append(dict(start_time=0.0,
                               stop_time=(stim_onsets[0] - stim_dur),
                               sb='b',
                               sample_filename=stim_vals[0]))

        for i, onset in enumerate(stim_onsets):
            filename = str(stim_vals[i])
            trial_list.append(dict(start_time=onset,
                                   stop_time=(onset + stim_dur),
                                   sb='s',
                                   sample_filename=filename))
            # trial_list.append(dict(start_time=onset+bl_start, stop_time=onset+bl_end, sb='b',frq=frq,amp=amp))

        # Add the period after the last stimulus to  baseline
        trial_list.append(dict(start_time=(stim_onsets[-1] + bl_end),
                               stop_time=rec_end_time,
                               sb='b',
                               sample_filename=stim_vals[-1]))

        return trial_list
