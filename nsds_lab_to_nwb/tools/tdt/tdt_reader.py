import logging.config
import tdt

logger = logging.getLogger(__name__)


stream_alternatives = {'ECoG': 'Wave'}


class TDTReader:
    """TDT interface

    Parameters
    ----------
    path: str
        Path to TDT folder
    channels: list, optional
        List of channel ids to import. Defaults to None.
    """
    def __init__(self, path, channels=None):
        self.path = path
        self.channels = channels

        if channels is None:
            self.tdt_obj = tdt.read_block(path)
        else:
            self.tdt_obj = tdt.read_block(path, channel=channels)

        self.streams = self.get_streams()
        self.block_name = self.tdt_obj['info']['blockname']
        self.start_time = self.tdt_obj['info']['utc_start_time']

        logger.debug('Streams: ' + ', '.join(self.streams))

    def get_streams(self):
        """Get TDT all stream names

        Returns:
            streams (list): stream names
        """
        streams = list(self.tdt_obj['streams'].keys())
        return streams

    def get_metadata(self, stream):
        """Get specified stream metadata

        Args:
            stream (string): stream name

        Returns:
            meta (dict): dictionary containing stream recording parameters (if no stream returns None)
        """
        stream = self.check_stream(stream)
        meta = {}
        meta['sample_rate'] = self.tdt_obj['streams'][stream]['fs']
        meta['channel_ids'] = self.tdt_obj['streams'][stream]['channel']
        meta['start_time'] = self.tdt_obj['info']['utc_start_time']
        data_shape = self.tdt_obj['streams'][stream]['data'].shape
        if len(data_shape) == 1:
            meta['num_samples'] = data_shape[0]
            meta['num_channels'] = 1
        else:
            meta['num_channels'], meta['num_samples'] = data_shape
        return meta

    def check_stream(self, stream):
        """Checks to see if user specified stream (or alternative name) exists in data.

        Parameters
        ----------
        stream: str
            Stream name.

        Returns
        -------
        stream: str
            Stream name updated to the standard name if an alternative was used.
        """
        error_message = f"Device or stream '{stream}' not found. Available streams: ["
        error_message += ", ".join(self.streams)
        error_message += "]"
        if stream not in self.streams:
            if stream not in stream_alternatives.keys():
                raise ValueError(error_message)
            else:
                stream = stream_alternatives[stream]
        return stream

    def get_data(self, *, stream=None, dev_conf=None):
        """Get specified data

        Parameters
        ----------
        stream: str
            Stream name
        dev_conf: (dict) metadata for the device.
            nwb_builder.metadata['device'][device_name]. Not used for TDT.

        Returns
        -------
        data: ndarray
            Data array
        meta: dict
            Meta data for the data array.
        """
        stream = self.check_stream(stream)
        data = self.tdt_obj['streams'][stream]['data'].T
        meta = self.get_metadata(stream)
        return data, meta

    def get_events(self):
        """Get event onset markers

        Returns:
            events (list): list of samples where an event occured
        """
        events = self.tdt_obj['epocs']['mark']['onset']
        return events
