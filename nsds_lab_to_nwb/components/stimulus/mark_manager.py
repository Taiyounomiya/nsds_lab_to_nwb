import logging

from nsds_lab_to_nwb.components.stimulus.utils import detect_events

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MarkManager():
    def __init__(self, rec_manager, stim_configs, use_tdt_mark_events=False):
        self.rec_manager = rec_manager
        self.stim_configs = stim_configs
        self.use_tdt_mark_events = use_tdt_mark_events

    def get_mark_track(self):
        # read recorded mark tracks
        mark_track, mark_rate = self.rec_manager.read_marks()

        # detect marked event times
        if self.rec_manager.rec_source == 'tdt' and self.use_tdt_mark_events:
            mark_events = self.rec_manager.read_mark_events()
        else:
            mark_events = None
        mark_events = self.get_mark_events(mark_events, mark_track, mark_rate)

        return mark_track, mark_rate, mark_events

    def get_mark_events(self, mark_events_input, mark_data, mark_rate):
        if mark_events_input is not None:
            # loaded directly from TDT object
            # (now suppressed by use_tdt_mark_events=False because wn2 requires re-detection)
            logger.info('Using marker events directly loaded from TDT')
            logger.debug(f'found {len(mark_events_input)} mark events')
            return mark_events_input

        logger.info('Detecting stimulus onsets by thresholding the mark track')
        stim_duration = self.stim_configs.get('duration', None)
        mark_threshold = self.stim_configs['mark_threshold']
        mark_events = detect_events(mark_data, mark_rate, mark_threshold,
                                    min_separation=stim_duration)
        logger.debug(f'found {len(mark_events)} mark events')
        return mark_events
