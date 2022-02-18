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
                  *, audio_play_length, rec_end_time, **unused_metadata):
        first_mark = self.stim_configs['first_mark']
        audio_end_time = (stim_onsets[0] - first_mark) + audio_play_length

        trial_list = []

        # Add the pre-stimulus period to baseline
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b',
                               sample_filename='none'))

        for i, onset in enumerate(stim_onsets):
            filename = str(stim_vals[i])
            try:
                stop_time = stim_onsets[i + 1]
            except IndexError:
                stop_time = audio_end_time
            trial_list.append(dict(start_time=onset,
                                   stop_time=stop_time,
                                   sb='s',
                                   sample_filename=filename))

        # Add the period after the last stimulus to baseline
        trial_list.append(dict(start_time=audio_end_time,
                               stop_time=rec_end_time,
                               sb='b',
                               sample_filename='none'))

        return trial_list
