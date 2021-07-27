import os
import unittest
import uuid

from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject

from nsds_lab_to_nwb.common.time import get_current_time, get_default_time
from nsds_lab_to_nwb.utils import get_software_info


class TestCase_NWBFile_Root(unittest.TestCase):

    dummy_time = get_default_time()
    current_time = get_current_time()

    output_file = '_test/test.nwb'

    def test_nwbfile_source_script(self):
        ''' test NWBFile construction '''

        # source_script, in plain text
        info = get_software_info()
        source_script = (f"Created by nsds-lab-to-nwb {info['version']} "
                         f"({info['url']}) "
                         f"(git@{info['git_describe']})")

        # do we also need this when source_script is used?
        source_script_file_name = os.path.basename(__file__)
        # print(f'source_script_file_name={source_script_file_name}')

        nwb_content = NWBFile(
            session_description='session description text',
            experimenter='experimenter',
            lab='Bouchard Lab',
            institution='LBNL',
            session_start_time=self.dummy_time,
            file_create_date=self.current_time,
            identifier=str(uuid.uuid1()),
            session_id='RFLYY_BXX',
            experiment_description='experiment description text',
            subject=Subject(
                subject_id='animal name',
                description='animal description',
                genotype='animal genotype',
                sex='animal sex',
                species='animal species',
                weight='animal weight',
            ),
            notes='note in plain text',
            pharmacology='pharmacology note in plain text',
            surgery='surgery note in plain text',
            source_script=source_script,
            source_script_file_name=source_script_file_name,
        )

        with NWBHDF5IO(path=self.output_file, mode='w') as nwb_fileIO:
            nwb_fileIO.write(nwb_content)


if __name__ == '__main__':
    unittest.main()
