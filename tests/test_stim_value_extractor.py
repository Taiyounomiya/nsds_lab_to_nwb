from nsds_lab_to_nwb.utils import get_stim_lib_path, get_metadata_lib_path

import pytest


stim_lib_path = get_stim_lib_path()
metadata_lib_path = get_metadata_lib_path()


def __test_stim(stim_name_input):
    """
    from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
    from nsds_lab_to_nwb.common.io import read_yaml
    import os
    stim_name, stim_info = check_stimulus_name(stim_name_input)
    stim_yaml_path = os.path.join(metadata_lib_path, 'auditory', 'yaml',
                                  'stimulus', stim_name + '.yaml')
    stim_configs = read_yaml(stim_yaml_path)
    sve = StimValueExtractor(stim_configs, stim_lib_path)
    stim_values = sve.extract()
    stim_values = None
    return stim_values
    """


@pytest.mark.xfail
def test_white_noise_stimuli():
    stim_name = 'wn2'
    stim_values = __test_stim(stim_name)
    assert stim_values is not None


@pytest.mark.xfail
def test_tone_stimuli():
    stim_name = 'tone'
    stim_values = __test_stim(stim_name)
    assert stim_values is not None

    stim_name = 'tone150'
    stim_values = __test_stim(stim_name)
    assert stim_values is not None


@pytest.mark.xfail
def test_timit_stimuli():
    stim_name = 'timit'
    stim_values = __test_stim(stim_name)
    assert stim_values is not None


@pytest.mark.xfail
def test_dmr_stimuli():
    stim_name = 'dmr'
    stim_values = __test_stim(stim_name)
    assert stim_values is None
