from nsds_lab_to_nwb.common.data_scanners import Dataset, AuditoryDataScanner

import pytest


# raw data path
data_path = '/clusterfs/NSDS_data/hackathon20201201/'

# new base?
data_path_tdt = '/clusterfs/NSDS_data/hackathon20201201/TTankBackup/'

@pytest.mark.xfail
def test_auditory_data_scanner_case1_old_data(self):
    ''' scan data_path and identify relevant subdirectories '''
    animal_name = 'R56'
    block = 'B13'
    data_scanner = AuditoryDataScanner(
        animal_name, block, data_path=self.data_path)
    # TODO: if there is any error, it should be raised through data_scanner
    # for now no validation is done
    dataset = data_scanner.extract_dataset()
    if not isinstance(dataset, Dataset):
        raise TypeError('expecting a custom Dataset object')

@pytest.mark.xfail
def test_auditory_data_scanner_case2_new_data(self):
    ''' scan data_path and identify relevant subdirectories '''
    animal_name = 'RVG02'
    block = 'B09'
    data_scanner = AuditoryDataScanner(
        animal_name, block, data_path=self.data_path_tdt)
    # TODO: if there is any error, it should be raised through data_scanner
    # for now no validation is done
    dataset = data_scanner.extract_dataset()
    if not isinstance(dataset, Dataset):
        raise TypeError('expecting a custom Dataset object')
