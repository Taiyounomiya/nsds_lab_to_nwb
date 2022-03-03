import logging
import numpy as np

from pynwb import TimeSeries

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MarkManager():
    def __init__(self, rec_manager, stim_configs, use_tdt_mark_events=False):
        self.rec_manager = rec_manager
        self.stim_configs = stim_configs
        self.mark_obj_name = 'stim_onset_marks'  # 'recorded_mark' (previous name)
        self.use_tdt_mark_events = use_tdt_mark_events

    def get_mark_track(self):
        # read recorded mark tracks, and create the mark timeseries
        mark_track, rate = self.rec_manager.read_marks()
        starting_time = 0.0    # because this is recorded mark, always starting at rec t=0
        mark_time_series = TimeSeries(name=self.mark_obj_name,
                                      data=mark_track,
                                      unit='Volts',
                                      starting_time=starting_time,
                                      rate=rate,
                                      description='Recorded mark that tracks stimulus onsets.')

        # detect marked event times
        if self.rec_manager.rec_source == 'tdt' and self.use_tdt_mark_events:
            mark_events = self.rec_manager.read_mark_events()
        else:
            mark_events = None
        mark_events = self.get_mark_events(mark_events, mark_time_series)

        return mark_time_series, mark_events

    def get_mark_events(self, mark_events_input, mark_time_series):
        if mark_events_input is not None:
            # loaded directly from TDT object
            # (now suppressed by use_tdt_mark_events=False because wn2 requires re-detection)
            logger.info('Using marker events directly loaded from TDT')
            logger.debug(f'found {len(mark_events_input)} mark events')
            return mark_events_input

        logger.info('Detecting stimulus onsets by thresholding the mark track')
        mark_rate = mark_time_series.rate
        stim_duration = self.stim_configs.get('duration', None)
        mark_threshold = self.stim_configs['mark_threshold']
        mark_events = detect_events(mark_time_series.data[:],
                                    mark_rate, mark_threshold,
                                    min_separation=stim_duration)
        logger.debug(f'found {len(mark_events)} mark events')
        return mark_events


def detect_events(mark_data, mark_rate, mark_threshold, min_separation=None):
    mark_front_padded = np.concatenate((np.array([0.]), mark_data), axis=0)
    thresh_crossings = np.diff((mark_front_padded > mark_threshold).astype('int'),
                               axis=0)
    mark_events_idx = np.where(thresh_crossings > 0.5)[0]
    mark_events = mark_events_idx / mark_rate

    if min_separation is not None:
        # if two adjacent marks are too close, drop the latter one
        too_close = np.where((mark_events[1:] - mark_events[:-1])
                             < min_separation)[0] + 1
        mark_events = np.delete(mark_events, too_close)

    return mark_events
