import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class ToneTokenizer(BaseTokenizer):
    """
    Tokenize tone pip stimulus data

    Original version author: Max Dougherty <maxdougherty@lbl.gov>
    As part of MARS
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)

        # list of ('column_name', 'column_description')
        self.custom_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                        ('frq', 'Stimulus Frequency'),
                        ('amp', 'Stimulus Amplitude')]

    def _tokenize(self, stim_vals, stim_onsets,
                  *, stim_dur, bl_start, bl_end, rec_end_time):
        trial_list = []

        # Add the pre-stimulus period to baseline
        trial_list.append(dict(start_time=0.0,
                                stop_time=stim_onsets[0]-stim_dur,
                                sb='b',
                                frq=str(float(stim_vals[0, 1])),
                                amp=str(float(stim_vals[0, 0]))))

        # TODO: Assert that the # of stim vals is equal to the number of found onsets
        assert len(stim_onsets)==len(stim_vals), (
                    "Incorrect number of stimulus onsets found."
                    + " Expected {:d}, found {:d}.".format(len(stim_vals), len(stim_onsets))
                    + " Perhaps you are not using the correct tokenizer?"
                    )
        for i, onset in enumerate(stim_onsets):
            frq = str(stim_vals[i, 1])
            amp = str(stim_vals[i, 0])
            trial_list.append(dict(start_time=onset, stop_time=onset+stim_dur,
                                    sb='s', frq=frq, amp=amp))
            if bl_start==bl_end:
                continue
            trial_list.append(dict(start_time=onset+bl_start, stop_time=onset+bl_end,
                                    sb='b', frq=frq, amp=amp))

        # Add the period after the last stimulus to  baseline
        trial_list.append(dict(start_time=stim_onsets[-1]+bl_end, stop_time=rec_end_time,
                                sb='b', frq=frq, amp=amp))

        return trial_list

    def _get_stim_onsets(self, mark_dset):
        mark_fs = mark_dset.rate
        mark_offset = self.stim_configs['mark_offset']
        stim_dur = self.stim_configs['duration']

        mark_trk, mark_threshold = self._get_mark_threshold(mark_dset)
        thresh_crossings = np.diff( (mark_trk > mark_threshold).astype('int'), axis=0)
        stim_onsets = np.where(thresh_crossings > 0.5)[0] + 1
        return (stim_onsets / mark_fs) + mark_offset
