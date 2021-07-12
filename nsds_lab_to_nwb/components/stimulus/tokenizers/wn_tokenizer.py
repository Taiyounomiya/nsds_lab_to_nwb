import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class WNTokenizer(BaseTokenizer):
    """
    Tokenize white noise stimulus data

    Original version author: Vyassa Baratham <vbaratham@lbl.gov>
    As part of MARS
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'WNTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_columns = [('sb', 'Stimulus (s) or baseline (b) period')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, stim_dur, bl_start, bl_end, rec_end_time):
        """
        (caveat: docstring is outdated)

        Required: mark track

        Output: stim on/off as "wn"
                baseline as "baseline"
        """
        trial_list = []

        # Add the pre-stimulus period to baseline
        # trial_list.append(dict(start_time=0.0, stop_time=stim_onsets[0]-stim_dur, sb='b'))

        for onset in stim_onsets:
            trial_list.append(dict(start_time=onset, stop_time=onset+stim_dur, sb='s'))
            if bl_start==bl_end:
                continue
            trial_list.append(dict(start_time=onset+bl_start, stop_time=onset+bl_end, sb='b'))

        # Add the period after the last stimulus to  baseline
        # trial_list.append(dict(start_time=stim_onsets[-1]+bl_end, stop_time=rec_end_time, sb='b'))

        return trial_list

    def _get_stim_onsets(self, mark_dset):
        if 'Simulation' in self.block_name:
            # # (mars legacy code, now broken)
            # raw_dset = nwb_content.acquisition['ECoG']
            # end_time = raw_dset.data.shape[0] / raw_dset.rate
            # return np.arange(0.5, end_time, 1.0)
            raise NotImplementedError('not supported in nsds_lab_to_nwb')

        mark_fs = mark_dset.rate
        mark_offset = self.stim_configs['mark_offset']
        stim_dur = self.stim_configs['duration']
        stim_dur_samp = stim_dur*mark_fs

        mark_threshold = 0.25 if self.stim_configs.get('mark_is_stim') else self.stim_configs['mark_threshold']
        thresh_crossings = np.diff( (mark_dset.data[:] > mark_threshold).astype('int'), axis=0 )
        stim_onsets = np.where(thresh_crossings > 0.5)[0] + 1 # +1 b/c diff gets rid of 1st datapoint

        real_stim_onsets = [stim_onsets[0]]
        for stim_onset in stim_onsets[1:]:
            # Check that each stim onset is more than 2x the stimulus duration since the previous
            if stim_onset > real_stim_onsets[-1] + 2*stim_dur_samp:
                real_stim_onsets.append(stim_onset)
        stim_onsets = (np.array(real_stim_onsets) / mark_fs) + mark_offset
        return stim_onsets

    def _validate_num_stim_onsets(self, stim_vals, stim_onsets):
        # NOTE: stim_vals is not used here
        num_onsets = len(stim_onsets)
        num_expected_trials = self.stim_configs['nsamples']
        if num_onsets != num_expected_trials:
            # print("WARNING: found {} stim onsets in block {}, but supposed to have {} samples".format(
            #     len(stim_onsets), self.block_name, self.stim_configs['nsamples']))
            print(f"[WARNING] {self.tokenizer_type}: "
                + "Incorrect number of stimulus onsets found "
                + f"in block {self.block_name}. "
                + f"Expected {num_expected_trials}, found {num_onsets}.")
