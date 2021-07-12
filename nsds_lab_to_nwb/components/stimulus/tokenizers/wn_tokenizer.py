import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.stimulus_tokenizer import StimulusTokenizer


class WNTokenizer(StimulusTokenizer):
    """
    Tokenize white noise stimulus data

    Original version author: Vyassa Baratham <vbaratham@lbl.gov>
    As part of MARS
    """
    def __init__(self, block_name, stim_configs):
        StimulusTokenizer.__init__(self, block_name, stim_configs)

        # list of ('column_name', 'column_description')
        self.custom_columns = [('sb', 'Stimulus (s) or baseline (b) period')]

    def tokenize(self, nwb_content, mark_name='recorded_mark'):
        """
        Required: mark track

        Output: stim on/off as "wn"
                baseline as "baseline"
        """
        if self._already_tokenized(nwb_content):
            return

        stim_onsets = self.__get_stim_onsets(nwb_content, mark_name)
        stim_dur = self.stim_configs['duration']
        bl_start = self.stim_configs['baseline_start']
        bl_end = self.stim_configs['baseline_end']

        self._add_trial_columns(nwb_content)

        # Add the pre-stimulus period to baseline
        # nwb_content.add_trial(start_time=0.0, stop_time=stim_onsets[0]-stim_dur, sb='b')

        for onset in stim_onsets:
            nwb_content.add_trial(start_time=onset, stop_time=onset+stim_dur, sb='s')
            if bl_start==bl_end:
                continue
            nwb_content.add_trial(start_time=onset+bl_start, stop_time=onset+bl_end, sb='b')

        # Add the period after the last stimulus to  baseline
        # rec_end_time = self._get_end_time(nwb_content, mark_name)
        # nwb_content.add_trial(start_time=stim_onsets[-1]+bl_end, stop_time=rec_end_time, sb='b')

    def __get_stim_onsets(self, nwb_content, mark_name):
        if 'Simulation' in self.block_name:
            raw_dset = self.read_raw('ECoG')
            end_time = raw_dset.data.shape[0] / raw_dset.rate
            return np.arange(0.5, end_time, 1.0)

        mark_dset = self.read_mark(nwb_content, mark_name)
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

        if len(real_stim_onsets) != self.stim_configs['nsamples']:
            print("WARNING: found {} stim onsets in block {}, but supposed to have {} samples".format(
                len(real_stim_onsets), self.block_name, self.stim_configs['nsamples']))

        return (np.array(real_stim_onsets) / mark_fs) + mark_offset
