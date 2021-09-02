import os, pytest
from nsds_lab_to_nwb.nwb_builder import NWBBuilder
from nsds_lab_to_nwb.utils import (split_block_folder, get_data_path,
                                   get_metadata_lib_path)

# Set to standard catscan locations (ignore any personal settings)
os.environ['NSDS_DATA_PATH'] = '/clusterfs/NSDS_data/raw/'
os.environ['NSDS_METADATA_PATH'] = '/clusterfs/NSDS_data/NSDSLab-NWB-metadata/'
os.environ['NSDS_STIMULI_PATH'] = '/clusterfs/NSDS_data/stimuli/'

RESAMPLE_DATA = True


@pytest.mark.parametrize("block_folder", [("RVG16_B01"),  # wn2
                                          ("RVG16_B02"),  # tone_diagnostic
                                          ("RVG16_B03"),  # wn2
                                          ("RVG16_B04"),  # tone_diagnostic
                                          ("RVG16_B05"),  # tone_diagnostic
                                          ("RVG16_B06"),  # tone
                                          ("RVG16_B07"),  # tone150
                                          ("RVG16_B08"),  # TIMIT, *bad block*
                                          ("RVG16_B09"),  # no stim, *bad block*
                                          ("RVG16_B10"),  # dmr
                                          ("RVG21_B12"),  # baseline stim
                                          ("RVG21_B13"),  # TIMIT
                                          ])
def test_nwb_builder(tmpdir, block_folder):
    """Runs the NWB pipline on a block."""
    if not os.path.isdir(os.environ['NSDS_DATA_PATH']):
        pytest.xfail('Testing data folder on catscan not found')

    _, animal_name, _ = split_block_folder(block_folder)
    data_path = get_data_path()
    block_metadata = os.path.join(data_path, animal_name, block_folder, f"{block_folder}.yaml")

    nwb_builder = NWBBuilder(
        data_path=data_path,
        block_folder=block_folder,
        save_path=tmpdir,
        block_metadata_path=block_metadata,
        resample_data=RESAMPLE_DATA)

    # build the NWB file content
    nwb_content = nwb_builder.build()

    # write to file
    nwb_builder.write(nwb_content)


@pytest.mark.parametrize("block_folder", [("R56_B10"),      # tone, *legacy block*
                                          ("R56_B13")])     # wn2, *legacy block*
def test_legacy_nwb_builder(tmpdir, block_folder):
    """Runs the NWB pipline on a block."""
    if not os.path.isdir(os.environ['NSDS_DATA_PATH']):
        pytest.xfail('Testing data folder on catscan not found')

    _, animal_name, _ = split_block_folder(block_folder)
    data_path = get_data_path()
    metadata_path = get_metadata_lib_path()
    block_metadata = os.path.join(metadata_path, "auditory", "legacy", "yaml", "block",
                                  animal_name, f"{block_folder}.yaml")

    nwb_builder = NWBBuilder(
        data_path=data_path,
        block_folder=block_folder,
        save_path=tmpdir,
        block_metadata_path=block_metadata,
        resample_data=RESAMPLE_DATA)

    # build the NWB file content
    nwb_content = nwb_builder.build()

    # write to file
    nwb_builder.write(nwb_content)
