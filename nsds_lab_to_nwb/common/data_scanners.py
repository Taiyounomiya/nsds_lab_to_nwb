import logging.config
import os

from nsds_lab_to_nwb.utils import (get_data_path, get_stim_lib_path,
                                   split_block_folder)

logger = logging.getLogger(__name__)


class Dataset():
    '''
    The Dataset class is just a convenient namespace for all the relevant paths
    where the input data can be found.
    See the DataScanner classes for how the Dataset is constructed.
    '''
    def __init__(self, block_folder, data_path, **path_kwargs):
        self.block_folder = block_folder
        self.data_path = data_path

        # store all paths
        for path_key, path_value in path_kwargs.items():
            setattr(self, path_key, path_value)


class DataScanner():
    '''
    Defines input path structure and stores relevant paths in a Dataset object.
    This is a base class for AuditoryDataScanner and BehaviorDataScanner classes.
    '''
    def __init__(self, block_folder,
                 data_path: str = '',
                 use_htk=False
                 ):
        self.data_path = data_path
        self.block_folder = block_folder
        self.data_path = get_data_path(data_path)
        self.surgeon_initials, self.animal_name, self.block_name = split_block_folder(block_folder)
        self.use_htk = use_htk

    def extract_dataset(self):
        ''' returns a Dataset object '''
        # should be implemented for the specific experiment type
        raise NotImplementedError()


class AuditoryDataScanner(DataScanner):
    def __init__(self, block_folder,
                 data_path: str = '',
                 stim_lib_path=None,
                 use_htk=False):
        # this sets self.animal_name, self.block_folder, and self.data_path
        super().__init__(block_folder, data_path=data_path, use_htk=use_htk)
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)

        logger.debug('AuditoryDataScanner...')

    def extract_dataset(self):
        kwargs = {'stim_lib_path': self.stim_lib_path}
        if self.use_htk:
            htk_path = self.__get_htk_path()
            if htk_path is not None:
                kwargs['htk_path'] = htk_path
            mark_path = self.__find_htk_mark_track()
            if mark_path is not None:
                kwargs['htk_mark_path'] = mark_path
        else:
            tdt_path = self.__get_tdt_path()
            if tdt_path is not None:
                kwargs['tdt_path'] = tdt_path
        return Dataset(self.block_folder,
                       data_path=self.data_path,
                       **kwargs)

    def __find_htk_mark_track(self, mark='mrk11.htk'):
        path = os.path.join(self.add_block_subdir(self.data_path), mark)
        if not os.path.exists(path):
            path = None
        return path

    def __get_htk_path(self, raw='RawHTK'):
        path = os.path.join(self.add_block_subdir(self.data_path), raw)
        if not os.path.exists(path):
            path = None
        return path

    def __get_tdt_path(self):
        path = self.add_block_subdir(self.data_path)
        if not os.path.exists(path):
            path = None
        return path

    def add_block_subdir(self, path):
        return os.path.join(path, self.animal_name, self.block_folder)


class BehaviorDataScanner(DataScanner):
    def __init__(self, animal_name, block,
                 data_path: str = '',
                 video_path=None,
                 ):
        DataScanner.__init__(self, animal_name, block, data_path=data_path)
        # this sets self.animal_name, self.block, and self.data_path

        # TODO: collect and pass relevant subdirectories. maybe video_path?
        self.video_path = video_path or os.path.join(self.data_path, 'Video/') # <<<< replace accordingly

    def extract_dataset(self):
        # TODO for behavior (reaching) data
        raise NotImplementedError()
