import logging

from nsds_lab_to_nwb.tools.htk.htk_reader import HTKReader
from nsds_lab_to_nwb.tools.htk.readers.htkfile import HTKFile
from nsds_lab_to_nwb.tools.tdt.tdt_reader import TDTReader

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RecManager():
    def __init__(self, dataset):
        self.dataset = dataset

        if hasattr(self.dataset, 'htk_mark_path'):
            logger.info('Using HTK')
            self.rec_source = 'htk'
            self.rec_reader = HTKReader(self.dataset.htk_path)
        else:
            logger.info('Using TDT')
            self.rec_source = 'tdt'
            self.rec_reader = TDTReader(self.dataset.tdt_path)

    def read_info(self):
        if self.rec_source == 'htk':
            return None

        return self.rec_reader.tdt_obj['info']

    def read_neural_data(self, stream, dev_conf):
        data, metadata = self.rec_reader.get_data(stream=stream, dev_conf=dev_conf)
        return data, metadata

    def read_marks(self):
        # Read the mark track
        if self.rec_source == 'htk':
            mark_file = HTKFile(self.dataset.htk_mark_path)
            mark_track, meta = mark_file.read_data()
            rate = mark_file.sample_rate
        else:
            mark_track, meta = self.rec_reader.get_data(stream='mrk1')
            rate = meta['sample_rate']
        return mark_track, rate

    def read_mark_events(self):
        if self.rec_source == 'htk':
            return None

        # for tdt
        try:
            return self.rec_reader.get_events()
        except AttributeError:
            # there is no mark for baseline (no stimulus) block
            return None
