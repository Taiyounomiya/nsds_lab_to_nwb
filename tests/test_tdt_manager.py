from tdt_manager import TdtManager
from pynwb import NWBHDF5IO

from datetime import datetime
from dateutil.tz import tzlocal
from pynwb import NWBFile

"""
Created on Tue Dec  8 20:57:11 2020

@author: jhermiz
"""

data_directory = '/home/jhermiz/data/hackathon20201201/TTankBackup/R56/R56_B13'
tdt = TdtManager(data_directory, verbose=True)

nwbfile = NWBFile('my first synthetic recording', 'EXAMPLE_ID', datetime.now(tzlocal()),
                  experimenter='Dr. Bilbo Baggins',
                  lab='Bag End Laboratory',
                  institution='University of Middle Earth at the Shire',
                  experiment_description='I went on an adventure with thirteen dwarves to reclaim vast treasures.',
                  session_id='LONELYMTN')
device = nwbfile.create_device(name='trodes_rig123')
electrode_name = 'tetrode1'
description = "an example tetrode"
location = "somewhere in the hippocampus"

electrode_group = nwbfile.create_electrode_group(electrode_name,
                                                 description=description,
                                                 location=location,
                                                 device=device)

for idx in [1, 2, 3, 4]:
    nwbfile.add_electrode(id=idx,
                          x=1.0, y=2.0, z=3.0,
                          imp=float(-idx),
                          location='CA1', filtering='none',
                          group=electrode_group)
electrode_table_region = nwbfile.create_electrode_table_region([0, 2], 'the first and third electrodes')

eseries = tdt.extract_tdt('ECoG', None, electrode_table_region)

nwbfile.add_acquisition(eseries)

# Write the data to file
io = NWBHDF5IO('test.nwb', 'w')
io.write(nwbfile)
io.close()
