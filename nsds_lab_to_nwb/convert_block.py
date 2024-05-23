import logging.config

from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path,
                                   get_stim_lib_path)
from nsds_lab_to_nwb.nwb_builder import NWBBuilder

def preprocess_block(nwb_path,
                     acq_name='ECoG',
                     initial_resample_rate=3200.,
                     final_resample_rate=400.,
                     filters='rat',
                     hg_only=True,
                     all_steps=False,
                     logger=None):
    """This is the default preprocessing pipeline.

    Perform the following steps:
    1) Resample to initial_resample_rate,
    2) Remove 60Hz noise and remove the CAR, and
    3) Perform and store a wavelet decomposition.
    4) Optionally resample the wavelet amplitudes.

    Parameters
    -------
    nwb_path : str or pathlike
        Path to the .nwb file. This file will be modified as a result of this function.
    acq_name : str
        Name of the acquisition, either 'ECoG' or 'Poly'.
    initial_resample_rate : float
        Frequency (in Hz) to resample to before performing wavelet transform.
    final_resample_rate : float
        Frequency (in Hz) to resample to after calculating wavelet amplitudes.
    filters : str
        Type of filter bank to use for wavelets. Choose from ['rat', 'human', 'changlab'].
    hg_only : bool
        Whether to store high gamma bands only. If False, use all filters.
    all_steps : bool
        Whether to store intermediate data between preprocessing steps.
    logger : logger
        Optional logger passed from upstream.

    Returns
    -------
    Returns nothing, but changes the NWB file at nwb_path.
    A ProcessingModule with name 'preprocessing' will be added to the NWB.
    """
    with NWBHDF5IO(nwb_path, 'a') as io:
        if logger is not None:
            logger.info('==================================')
            logger.info(f'Running preprocessing for {nwb_path}.')

        nwbfile = io.read()
        try:
            electrical_series = nwbfile.acquisition[acq_name]
        except KeyError:
            # in case NWB file is in a legacy format
            electrical_series = nwbfile.acquisition['Raw'][acq_name]

        nwbfile.create_processing_module(name='preprocessing',
                                         description='Preprocessing.')
        if all_steps:
            if logger is not None:
                logger.info('Resampling...')
            _, electrical_series_ds = store_resample(electrical_series,
                                                     nwbfile.processing['preprocessing'],
                                                     initial_resample_rate)
            del _

            if logger is not None:
                logger.info('Filtering and re-referencing...')
            _, electrical_series_CAR = store_linenoise_notch_CAR(electrical_series_ds,
                                                                 nwbfile.processing['preprocessing'])
            del _
            series = electrical_series_CAR
        else:
            rate = electrical_series.rate
            if logger is not None:
                logger.info('Resampling...')
            ts = resample(electrical_series.data[:] * scaling,
                          initial_resample_rate, rate)
            if logger is not None:
                logger.info('Filtering and re-referencing...')
            ts = apply_linenoise_notch(ts, initial_resample_rate)
            ts = subtract_CAR(ts)
            electrical_series_CAR = ElectricalSeries('CAR_ln_downsampled_' + electrical_series.name,
                                                     ts,
                                                     electrical_series.electrodes,
                                                     starting_time=electrical_series.starting_time,
                                                     rate=initial_resample_rate)
            series = electrical_series

        if logger is not None:
            logger.info('Running wavelet transform...')
        _, electrical_series_wvlt = store_wavelet_transform(electrical_series_CAR,
                                                            nwbfile.processing['preprocessing'],
                                                            filters=filters,
                                                            hg_only=hg_only,
                                                            post_resample_rate=final_resample_rate,
                                                            source_series=series)

        io.write(nwbfile)
        if logger is not None:
            logger.info(f'Preprocessing added to {nwb_path}.')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULT_PREPROCESSING_KWARGS = {
    'initial_resample_rate': 3200., 'final_resample_rate': 400.,
    'filters': 'rat', 'hg_only': True}


def convert_block(block_folder: str,
                  save_path: str,
                  data_path=None,
                  stim_lib_path=None,
                  metadata_lib_path=None,
                  block_metadata_path=None,
                  metadata_save_path=None,
                  resample_data=True,
                  use_htk=False,
                  process_stim=True,
                  write_nwb=True,
                  add_preprocessing=False):
    '''Wrapper for converting a single block of data using NWBBuilder.
    '''
    logger.debug(f'Converting block {block_folder}')

    data_path = get_data_path(data_path)
    metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
    stim_lib_path = get_stim_lib_path(stim_lib_path)

    logger.debug(f'data_path={data_path}')
    logger.debug(f'metadata_lib_path={metadata_lib_path}')
    logger.debug(f'stim_lib_path={stim_lib_path}')
    logger.debug(f'save_path={save_path}')

    # create a builder for the block
    nwb_builder = NWBBuilder(block_folder=block_folder,
                             data_path=data_path,
                             save_path=save_path,
                             block_metadata_path=block_metadata_path,
                             metadata_save_path=metadata_save_path,
                             stim_lib_path=stim_lib_path,
                             resample_data=resample_data,
                             use_htk=use_htk)

    # build the NWB file content
    nwb_content = nwb_builder.build(process_stim=process_stim)

    # write to file
    if write_nwb:
        nwb_builder.write(nwb_content)
    else:
        logger.info('Finishing without writing to a file, because write_nwb is set to False.')

    if add_preprocessing:
        # use default parameters for preprocessing
        preprocess_block(nwb_builder.output_file,
                         acq_name='ECoG',   # for now ecog only?
                         **DEFAULT_PREPROCESSING_KWARGS,
                         logger=logger)
