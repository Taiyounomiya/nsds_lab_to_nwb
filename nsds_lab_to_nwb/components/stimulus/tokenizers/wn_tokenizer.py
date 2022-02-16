import logging
import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


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
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, stim_dur, bl_start, bl_end, rec_end_time, **unused_metadata):
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
            trial_list.append(dict(start_time=onset, stop_time=(onset + stim_dur), sb='s'))
            if bl_start == bl_end:
                continue
            trial_list.append(dict(start_time=(onset + bl_start), stop_time=(onset + bl_end), sb='b'))

        # Add the period after the last stimulus to  baseline
        # trial_list.append(dict(start_time=stim_onsets[-1]+bl_end, stop_time=rec_end_time, sb='b'))

        return trial_list

    def _get_stim_onsets(self, mark_time_series, mark_threshold=None):
        if 'Simulation' in self.block_name:
            # # (mars legacy code, now broken)
            # raw_dset = nwb_content.acquisition['ECoG']
            # end_time = raw_dset.data.shape[0] / raw_dset.rate
            # return np.arange(0.5, end_time, 1.0)
            raise NotImplementedError('not supported in nsds_lab_to_nwb')

        mark_fs = mark_time_series.rate
        stim_dur = self.stim_configs['duration']
        stim_dur_samp = stim_dur * mark_fs

        stim_onsets_idx = super()._get_stim_onsets(mark_time_series, mark_threshold=mark_threshold)

        # Check that each stim onset is more than 2x the stimulus duration since the previous
        minimal_interval = (2 * stim_dur_samp)
        stim_onsets_idx = self.__require_minimal_interval(stim_onsets_idx, minimal_interval)
        logger.debug(f'filtered to {len(stim_onsets_idx)} onsets')
        return stim_onsets_idx

    def _get_mark_threshold(self):
        # NOTE: this is only used when TDT-loaded mark onsets are not available.
        # see issue #102 for more discussion on mark thresholds.

        if self.stim_configs.get('mark_is_stim', False):
            # NOTE: this is true for stimulus wn1, but not wn2
            mark_threshold = 0.25  # this value takes priority
            logger.debug(f'using mark_threshold={mark_threshold} because mark_is_stim=True')
            return mark_threshold

        # by default use the value in stimulus metadata
        return super()._get_mark_threshold()

    def __require_minimal_interval(self, stim_onsets_idx, minimal_interval):
        real_stim_onsets_idx = []
        prev_onset_i = None
        for stim_onset_i in stim_onsets_idx:
            if (prev_onset_i is None) or (stim_onset_i - prev_onset_i > minimal_interval):
                real_stim_onsets_idx.append(stim_onset_i)
                prev_onset_i = stim_onset_i
        return np.array(real_stim_onsets_idx)

    def _validate_num_stim_onsets(self, stim_vals, stim_onsets):
        # NOTE: stim_vals is not used here
        num_onsets = len(stim_onsets)
        num_expected_trials = self.stim_configs['nsamples']
        mismatch_msg = (
            f"{self.tokenizer_type}: "
            + "Incorrect number of stimulus onsets found "
            + f"in block {self.block_name}. "
            + f"Expected {num_expected_trials}, found {num_onsets}.")

        if num_onsets != num_expected_trials:
            # NOTE: BaseTokenizer behavior is to raise a ValueError
            logger.warning(mismatch_msg)
