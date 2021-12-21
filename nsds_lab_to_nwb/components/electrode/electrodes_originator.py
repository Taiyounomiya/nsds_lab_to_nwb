import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ElectrodesOriginator():
    def __init__(self, metadata):
        self.metadata = metadata

    def make(self, nwb_content):
        logger.info('Creating devices...')
        self.__create_devices(nwb_content)
        logger.info('Creating electrode groups...')
        self.__create_electrode_groups(nwb_content)
        logger.info('Creating electrodes...')
        self.__add_electrodes(nwb_content)
        electrode_table_regions = self.__create_electrode_table_regions(nwb_content)
        return electrode_table_regions

    def __create_devices(self, nwb_content):
        ''' create devices '''
        for device_name, dev_conf in self.metadata['device'].items():
            if not isinstance(dev_conf, dict):
                # skip any extra items in metadata
                continue
            _ = nwb_content.create_device(
                name=device_name,
                description=dev_conf['descriptions']['device_description'],
                manufacturer=dev_conf['manufacturer'])
            logger.debug(f' - Created device {device_name}')

    def __create_electrode_groups(self, nwb_content):
        ''' create electrode groups '''
        for device_name, device in nwb_content.devices.items():
            # in our case, only one ElectrodeGroup per device;
            # therefore ElectrodeGroup name is the same as device name
            dev_conf = self.metadata['device'][device_name]
            description = dev_conf['descriptions']['electrode_group_description']
            location = dev_conf['location']
            _ = nwb_content.create_electrode_group(
                name=device_name,
                device=device,
                description=description,
                location=location)
            logger.debug(f' - Created an electrode group for device {device_name}')
            logger.debug(f'   Description: {description}')
            logger.debug(f'   Location: {location}')

    def __add_electrodes(self, nwb_content):
        for device_name in nwb_content.devices:
            e_group = nwb_content.electrode_groups[device_name]
            dev_conf = self.metadata['device'][device_name]

            # Add column for bad electrodes
            # Check whether electrodes table has already been made
            if nwb_content.electrodes is None:
                bad_desc = 'Whether an electrode was determined to be unusable '\
                    'during real time data'
                nwb_content.add_electrode_column('bad', bad_desc)

            # Add each electrode
            for _, ch in dev_conf['ch_map'].items():
                bad_chs = dev_conf['bad_chs']
                bad_flag = np.isin(ch['electrode_id'], bad_chs)
                nwb_content.add_electrode(
                    id=ch['electrode_id'],
                    x=np.nan,
                    y=np.nan,
                    z=np.nan,
                    rel_x=ch['x'],
                    rel_y=ch['y'],
                    rel_z=ch['z'],
                    location=dev_conf['location'],
                    imp=dev_conf['imp'],
                    filtering=dev_conf['filtering'],
                    group=e_group,
                    bad=bad_flag)
            logger.debug(f' - Added all electrodes for electrode group {device_name}')

    def __create_electrode_table_regions(self, nwb_content):
        e_regions = {}
        for device_name in nwb_content.devices:
            # Collect device channel IDs for electrode table region
            ch_map = self.metadata['device'][device_name]['ch_map']
            electrode_region = [ch_map[i]['electrode_id'] for i in ch_map]

            # Create the electrode table region for this device
            table_region = nwb_content.create_electrode_table_region(
                region=electrode_region,
                description=f'Electrode table region for device {device_name}')
            e_regions[device_name] = table_region
        return e_regions
