from nsds_lab_to_nwb.common.io import read_mat_file
from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class ToneTokenizer(BaseTokenizer):
    """
    Tokenize into discrete tone pip stimulus trials.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'ToneTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('frq', 'Stimulus Frequency'),
                                     ('amp', 'Stimulus Amplitude')]

    def _load_stim_parameters(self):
        stim_params_path = self.stim_configs['stim_params_path']
        stim_vals = tone_stimulus_values(stim_params_path)
        return stim_vals

    def _tokenize(self, stim_vals, stim_onsets,
                  *, audio_start_time, audio_end_time, rec_end_time):
        bl_start = self.stim_configs['baseline_start']
        stim_dur = self.stim_configs['duration']
        bl_end = self.stim_configs['baseline_end']

        trial_list = []

        none_str = 'nan'    # for indicating baseline frq and amp

        # period before the first stimulus starts
        trial_list.append(dict(start_time=0.0,
                               stop_time=stim_onsets[0],
                               sb='b',
                               frq=none_str,
                               amp=none_str))

        for i, onset in enumerate(stim_onsets):
            frq = str(stim_vals[i, 1])
            amp = str(stim_vals[i, 0])

            # in-trial, pre-signal baseline
            start_time = onset
            stop_time = start_time + bl_start
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

            # actual signal
            start_time = stop_time
            stop_time = start_time + stim_dur
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='s',
                                   frq=frq,
                                   amp=amp))

            # in-trial, post-signal baseline
            start_time = stop_time
            stop_time = start_time + bl_end
            trial_list.append(dict(start_time=start_time,
                                   stop_time=stop_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

        # period after the end of last stim trial until recording stops
        if stop_time < rec_end_time:
            start_time = stop_time
            trial_list.append(dict(start_time=start_time,
                                   stop_time=rec_end_time,
                                   sb='b',
                                   frq=none_str,
                                   amp=none_str))

        return trial_list


def tone_stimulus_values(mat_file_path):
    """adapted from mars.configs.block_directory

    Parameters
    ----------
    mat_file_path : path
        full path to a .mat file that contains stim_values.

    Returns
    -------
    stim_vals : ndarray (n, 2)
        a 2D array with two columns (NOTE: changed from legacy behavior)
        `stim_vals[:, 0]` are the amplitudes,
        `stim_vals[:, 1]` are the frequencies of the tones.
    """
    sio = read_mat_file(mat_file_path)
    stim_vals = sio['stimVls'][:].astype(int)

    # check dimension
    shape = stim_vals.shape
    if not (len(shape) == 2) and (2 in shape):
        # should be a 2D array, with 2 columns or 2 rows
        raise ValueError('stim_vals dimension mismatch')
    if shape[0] == 2:
        # changed from legacy behavior (now 2 columns; was 2 rows in mars)
        stim_vals = stim_vals.T

    # this offset value comes from mars; what is this?
    # variable naming (amp_offset) was by JHB and could be wrong
    amp_offset = 8
    stim_vals[:, 0] = stim_vals[:, 0] + amp_offset

    return stim_vals
