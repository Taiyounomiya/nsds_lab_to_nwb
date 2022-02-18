import os
import numpy as np

from nsds_lab_to_nwb.common.io import read_mat_file
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name


class StimValueExtractor():
    def __init__(self, stim_configs, stim_lib_path):
        self.stim_name, self.stim_info = check_stimulus_name(stim_configs['name'])
        self.stim_type = stim_configs['type']
        self.stim_values_command = stim_configs.get('stim_values', None)
        self.stim_lib_path = stim_lib_path

    def extract(self):
        if self.stim_type == 'continuous':
            # this feature is only for discrete stimuli; skip
            return None

        # for synthetic stimuli
        if self.stim_values_command is not None:
            stim_values_command = self.stim_values_command
            if 'gen_tone_stim_vals' in stim_values_command:
                # for test_tone_stim
                stim_values = gen_tone_stim_vals()
            if 'np.ones' in stim_values_command:
                # for white noises
                stim_values = eval(stim_values_command)
            return stim_values

        # for tone and timit stimuli
        if 'tone' in self.stim_name:
            stim_values_path = self._get_stim_values_path()
            stim_values = tone_stimulus_values(stim_values_path)
            return stim_values
        if 'timit' in self.stim_name:
            stim_values_path = self._get_stim_values_path()
            stim_values = timit_stimulus_values(stim_values_path)
            return stim_values

        raise ValueError('Unknown input for stimulus parameterization')

    def _get_stim_values_path(self, path_from_metadata=None):
        # prioritize path from list_of_stimuli.yaml in this package
        path_from_los = self.stim_info['parameter_path']
        if len(path_from_los) > 0:
            return os.path.join(self.stim_lib_path, path_from_los)

        # if empty path in list_of_stimuli.yaml, use metadata input
        if path_from_metadata is not None:
            return os.path.join(self.stim_lib_path, path_from_metadata)

        return ValueError('No input for the path to stim parameterization info')


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


def timit_stimulus_values(file_path):
    """adapted from mars.configs.block_directory

    Parameters
    -----------
    file_path : full path to a .txt file that contains a list of filenames

    Returns
    --------
    stim_vals: list of str
        each item is a .wav file name in TIMIT. (should confirm!)
    """
    _, ext = os.path.splitext(file_path)
    if not (ext == '.txt'):
        raise ValueError('for now only accepting a txt file that lists wav file names.')

    # expecting a text file, one .wav filename string per row
    with open(file_path) as f:
        lines = f.readlines()
    stim_vals = [line.rstrip(' \n') for line in lines]
    return stim_vals


def gen_tone_stim_vals():
    ''' exact copy from mars.configs.block_directory

    Note: this is only used for test_tone_stim.yaml (see metadata repo)
    '''
    frqs = np.array([500, 577, 666, 769, 887, 1024, 1182,
                     1364, 1575, 1818, 2098, 2421, 2795, 3226, 3723,
                     4297, 4960, 5725, 6608, 7627, 8803, 10160, 11727,
                     13535, 15622, 18031, 20812, 24021, 27725, 32000])
    amps = np.arange(1, 9)
    frqset, ampset = np.meshgrid(frqs, amps)
    frq_amp_pairs = np.array([ampset.flatten(), frqset.flatten()]).T
    np.random.seed(seed=1234) # ensure that the same order is produced with each call.
    shuffle_inds1 = np.random.permutation(np.arange(frq_amp_pairs.shape[0]))
    shuffle_inds2 = np.random.permutation(np.arange(frq_amp_pairs.shape[0]))
    stim_vals = np.concatenate((frq_amp_pairs[shuffle_inds1, :],
                                frq_amp_pairs[shuffle_inds2, :]),
                               axis=0)
    return stim_vals.T
