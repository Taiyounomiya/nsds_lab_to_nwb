import logging
import os
import numpy as np
import itertools
from collections import OrderedDict

from nsds_lab_to_nwb.utils import (get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder, str2bool)

from nsds_lab_to_nwb.common.io import read_yaml, write_yaml
from nsds_lab_to_nwb.common.time import LOCAL_TIMEZONE, get_date_string_only
from nsds_lab_to_nwb.metadata.exp_note_reader import ExpNoteReader
from nsds_lab_to_nwb.metadata.keymap_helper import apply_keymap
from nsds_lab_to_nwb.metadata.resources import read_metadata_resource
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name


_DEFAULT_EXPERIMENT_TYPE = 'auditory'
_TDT_ECoG_CONVERSION = '1e-6'
_TDT_ECoG_RESOLUTION = '1e-6'
_TDT_Poly_CONVERSION = '1.'
_TDT_Poly_RESOLUTION = '1e-7'


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MetadataReader:
    ''' Reads metadata input for new experiments.
    '''

    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path: str,
                 block_folder: str,
                 metadata_save_path=None,
                 ):
        self.block_metadata_path = block_metadata_path
        self.metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
        self.block_folder = block_folder
        self.surgeon_initials, self.animal_name, self.block_tag = split_block_folder(block_folder)
        self.metadata_save_path = metadata_save_path

    def read(self):
        self.metadata_input = self.load_metadata_source()
        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_input.yaml',
                       self.metadata_input)

        self.parse()
        self.common_check()
        self.complete_notes()
        self.extra_cleanup()
        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_input_clean.yaml',
                       self.metadata_input)

        return self.metadata_input

    def load_metadata_source(self):
        try:
            metadata_input = read_yaml(self.block_metadata_path)
        except FileNotFoundError:
            # first generate the block metadata file
            block_path_full, block_metadata_file = os.path.split(self.block_metadata_path)
            experiment_path, _ = os.path.split(block_path_full)
            block_folder, ext = os.path.splitext(block_metadata_file)
            logger.debug(f'Looking for an experiment note file in {experiment_path}...')
            reader = ExpNoteReader(experiment_path, block_folder)
            reader.dump_yaml(write_path=self.block_metadata_path)
            # then try reading again
            metadata_input = read_yaml(self.block_metadata_path)
        return metadata_input

    def parse(self):
        self.metadata_input = apply_keymap(self.metadata_input.copy(),
                                           keymap_file='metadata_keymap')

    def common_check(self):
        ''' make sure that core fields exist before further expanding metadata components.
        common for both new and legacy pipelines.
        '''
        if 'subject' not in self.metadata_input:
            self.metadata_input['subject'] = {}
            self.metadata_input['subject']['subject_id'] = self.animal_name

        # fix subject weight unit - always 'g' in our case
        subject_metadata = self.metadata_input['subject']
        if 'weight' in subject_metadata:
            weight = str(subject_metadata['weight'])
            if 'g' not in weight:
                subject_metadata['weight'] = f'{weight}g'

        null_stim_name = None  # distinguish from intended stimulus-less session ("baseline")
        if 'stimulus' not in self.metadata_input:
            self.metadata_input['stimulus'] = {'name': null_stim_name}
        if 'name' not in self.metadata_input['stimulus']:
            self.metadata_input['stimulus']['name'] = null_stim_name
        stim_name = self.metadata_input['stimulus']['name']
        if not isinstance(stim_name, str) or stim_name in ('nan', '.nan'):
            self.metadata_input['stimulus']['name'] = null_stim_name

        if 'session_description' not in self.metadata_input:
            try:
                self.metadata_input['session_description'] = self.metadata_input['stimulus']['name']
            except KeyError:
                self.metadata_input['session_description'] = 'Unknown'

        device_metadata = self.metadata_input['device']
        for key in ('ECoG', 'Poly'):
            dev_conf = device_metadata[key]

            # required for ElectrodeGroup component - placeholders for now
            if 'description' not in dev_conf:
                dev_conf['descriptions'] = {}
            if 'location' not in dev_conf:
                # anatomical location in the brain
                dev_conf['location'] = ''

            # required for Electrode component
            if 'imp' not in dev_conf:
                # TODO: include impedance value
                dev_conf['imp'] = np.nan
            if 'filtering' not in dev_conf:
                # see discussion in issue #51
                dev_conf['filtering'] = (
                    'The signal is low pass filtered at 45 percent of the sample rate, '
                    'and high pass filtered at 2 Hz.')

            # check format of bad_chs
            if 'bad_chs' in dev_conf:
                if not isinstance(dev_conf['bad_chs'], list):
                    input_type = type(dev_conf['bad_chs']).__name__
                    logger.info(f'Expected a list of channel ids for {key}.bad_chs, '
                                f'but got {input_type}.')
                    dev_conf['bad_chs'] = self._fix_bad_chs_format(dev_conf['bad_chs'])

    def _fix_bad_chs_format(self, bad_chs):
        msg_when_failed = ('Unable to interpret bad_chs as a list. ' +
                           'Check your metadata input and ' +
                           'review the yaml syntax for storing a list.')

        if isinstance(bad_chs, str):
            logger.info(' - Trying to interpret the str...')
            # assume that this string has a list of integers separated by commas
            str_split = bad_chs.split(',')
            # remove spaces between commas
            bad_chs_list_strings = [x.strip() for x in str_split]
            try:
                bad_chs = [int(ch) for ch in bad_chs_list_strings]
                logger.info(' - Converted to a list of integers.')
                return bad_chs
            except ValueError:
                raise ValueError(msg_when_failed)
        elif np.isnan(bad_chs):
            bad_chs = []
            logger.info(' - Converted nan to empty list.')
            return bad_chs
        else:
            raise TypeError(msg_when_failed)

    def complete_notes(self):
        # TODO: store notes for all blocks for this animal, not just this one?
        self.__complete_surgery_note()

    def extra_cleanup(self):
        device_metadata = self.metadata_input['device']
        block_meta = self.metadata_input['block_meta']
        experiment_meta = self.metadata_input['experiment_meta']

        # validate and drop duplicate information
        block_id = block_meta.pop('block_id', None)
        block_tag_check = f'B{int(block_id):02d}'
        if (block_id is not None) and (self.block_tag != block_tag_check):
            raise ValueError(f'block id mismatch: {self.block_tag} vs. {block_tag_check}')

        animal_number = experiment_meta.pop('animal_number', None)
        animal_name_check = f'R{self.surgeon_initials}{int(animal_number):02d}'
        if (animal_number is not None) and (self.animal_name != animal_name_check):
            raise ValueError(f'animal number mismatch: {self.animal_name} vs. {animal_name_check}')

        # read the clean_block switch
        if 'is_clean_block' in block_meta:
            block_meta['is_clean_block'] = str2bool(block_meta['is_clean_block'])

        # if a device was not actually used in this block, drop the corresponding metadata
        default_value = False
        block_meta['has_ecog'] = str2bool(block_meta.get('has_ecog', default_value))
        block_meta['has_poly'] = str2bool(block_meta.get('has_poly', default_value))
        if not block_meta['has_ecog']:
            device_metadata.pop('ECoG')
        if not block_meta['has_poly']:
            device_metadata.pop('Poly')
            block_meta.pop('poly_ap_loc', None)
            block_meta.pop('poly_dev_loc', None)

        # Add conversion and resolution defaults if not there
        if 'ECoG' in device_metadata.keys():
            d = device_metadata['ECoG']
            if 'conversion' not in d.keys():
                if d['acq'] == 'TDT PZM5':
                    d['conversion'] = _TDT_ECoG_CONVERSION
            if 'resolution' not in d.keys():
                if d['acq'] == 'TDT PZM5':
                    d['resolution'] = _TDT_ECoG_CONVERSION
        if 'Poly' in device_metadata.keys():
            d = device_metadata['Poly']
            if 'conversion' not in d.keys():
                if d['acq'] == 'TDT PZM5':
                    d['conversion'] = _TDT_Poly_CONVERSION
            if 'resolution' not in d.keys():
                if d['acq'] == 'TDT PZM5':
                    d['resolution'] = _TDT_Poly_CONVERSION

        # make extra_meta
        self.metadata_input['extra_meta'] = {}
        for key in ('block_meta', 'experiment_meta', 'other'):
            self.metadata_input['extra_meta'].update(self.metadata_input.pop(key, {}))

    def __complete_surgery_note(self):
        experiment_meta = self.metadata_input['experiment_meta']
        surgery = self.metadata_input['surgery']

        if ('procedure_date' in experiment_meta):
            surgery_date = experiment_meta.pop('procedure_date')
            try:
                surgery_date = get_date_string_only(surgery_date)
            except ValueError:
                # datetime format error: just use input string as-is
                pass
            surgery += f'\nSurgery date: {surgery_date}'

        if ('procedure_time' in experiment_meta):
            surgery_time = experiment_meta.pop('procedure_time')
            surgery += f'\nSurgery time: {surgery_time} ({LOCAL_TIMEZONE})'

        if 'surgery_notes' in experiment_meta:
            surgery_notes = experiment_meta.pop('surgery_notes')
            surgery += f'\nSurgery notes: {surgery_notes}'

        if 'surgery_outcome' in experiment_meta:
            surgery_outcome = experiment_meta.pop('surgery_outcome')
            surgery += f'\nSurgery outcome: {surgery_outcome}'

        self.metadata_input['surgery'] = surgery


class LegacyMetadataReader(MetadataReader):
    ''' Reads metadata input for old experiments.
    '''

    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path: str,
                 block_folder: str,
                 metadata_save_path=None,
                 ):
        super().__init__(block_metadata_path, metadata_lib_path,
                         block_folder, metadata_save_path)

        self.experiment_type = 'auditory'   # for legacy auditory datasets

        # TODO: separate (experiment, device) metadata library as legacy
        self.legacy_lib_path = os.path.join(self.metadata_lib_path, self.experiment_type, 'legacy')

    def load_metadata_source(self):
        # direct input from the block yaml file (not yet expanded)
        metadata_input = read_yaml(self.block_metadata_path)

        # load from metadata library (legacy structure)
        for key in ('experiment', 'device'):
            logger.info(f'expanding {key} from legacy metadata library...')
            filename = metadata_input.pop(key)
            ref_data = read_yaml(
                os.path.join(self.legacy_lib_path, 'yaml', key, f'{filename}.yaml'))
            ref_data.pop('name', None)
            metadata_input.update(ref_data)

        # also load old experiment notes, if available
        animal_num = int(self.animal_name[1:])  # strip the leading 'R'
        animal_name_fixed = f'R{animal_num:02d}'
        exp_note_path = os.path.join(self.legacy_lib_path, 'exp_notes',
                                     f'{animal_name_fixed}_exp_note.txt')
        if os.path.exists(exp_note_path):
            # expecting a plain text file; read into a list of strings
            with open(exp_note_path) as f:
                exp_note_input = f.readlines()
        else:
            exp_note_input = []
        metadata_input['exp_note_input'] = exp_note_input

        return metadata_input

    def parse(self):
        self.metadata_input = apply_keymap(self.metadata_input.copy(),
                                           keymap_file='metadata_keymap_legacy')

    def complete_notes(self):
        self.__add_old_experiment_notes()

    def extra_cleanup(self):
        # fill in old subject information
        old_subject_input = read_metadata_resource('old_subject_metadata')
        old_subject_metadata = old_subject_input['subject_metadata']
        old_subject_metadata['weight'] = old_subject_input['weights'].get(self.animal_name, 'Unknown')
        for key in old_subject_metadata:
            if key not in self.metadata_input['subject']:
                self.metadata_input['subject'][key] = old_subject_metadata[key]

        # put bad_chs to right places
        device_metadata = self.metadata_input['device']
        bad_chs_dict = device_metadata.pop('bad_chs', None)
        if bad_chs_dict is not None:
            for dev_name, bad_chs in bad_chs_dict.items():
                device_metadata[dev_name]['bad_chs'] = bad_chs

        # data acquisition system
        if 'dac' in self.metadata_input:
            acq = self.metadata_input.pop('dac')
            for dev_name in ('ECoG', 'Poly'):
                if dev_name in device_metadata:
                    device_metadata[dev_name]['acq'] = acq

        # check and drop extra device information
        if 'comment' in device_metadata:
            dev_comment = device_metadata.pop('comment', '').strip(' ')
            # usually empty, but keep if there is content
            if len(dev_comment) > 0:
                for dev_name in ('ECoG', 'Poly'):
                    if dev_name in device_metadata:
                        device_metadata[dev_name]['comment'] = dev_comment

        if 'htk_meta' in self.metadata_input:
            # assuming that these are fixed (so no need to keep)
            _mark = 'mrk11.htk'
            _audio = 'aud11.htk'
            if self.metadata_input['htk_meta'].pop('mark', _mark) != _mark:
                raise ValueError('Unexpected filename for HTK mark. Perhaps we should keep this?')
            if self.metadata_input['htk_meta'].pop('audio', _audio) != _audio:
                raise ValueError('Unexpected filename for HTK audio. Perhaps we should keep this?')

        # make extra_meta
        self.metadata_input['extra_meta'] = {}
        for key in ('htk_meta', 'other'):
            self.metadata_input['extra_meta'].update(self.metadata_input.pop(key, {}))

        # final touches...
        if self.experiment_type == 'auditory':
            self.metadata_input['experiment_description'] = 'Auditory experiment'
        if ('session_description' not in self.metadata_input
                or len(self.metadata_input['session_description']) == 0):
            self.metadata_input['session_description'] = (
                'Auditory experiment with {} stimulus'.format(self.metadata_input['stimulus']['name']))

    def __add_old_experiment_notes(self):
        notes = self.metadata_input['notes'].strip(' ')
        if notes == 'TODO':
            notes = ''  # drop placeholder text
        if len(notes) > 0:
            notes += '\n\n'

        # store old experiment notes, for now as-is
        notes = f'# === Experiment note for {self.animal_name} (all blocks) ==='
        exp_note_input = self.metadata_input.get('exp_note_input')
        for row in exp_note_input:
            row_plain = row.strip(' \n').replace('\t', '..')
            notes += f'\n{row_plain}'

        self.metadata_input['notes'] = notes


class MetadataManager:
    """Manages metadata for NWB file builder

    Parameters
    ----------
    block_metadata_path : str
        Path to block metadata file.
    metadata_lib_path : str
        Path to metadata library repo.
    stim_lib_path : str
        Path to stimulus library.
    block_folder : str
        Block specification.
    metadata_save_path : str (optional)
        Path to a directory where parsed metadata file(s) will be saved.
        Files are saved only if metadata_save_path is provided.
    experiment_type : str (optional)
        Experiment type within the NSDS Lab: 'auditory' (default) or 'behavior'.
    legacy_block : bool (optional)
        Indicates whether this is a legacy block.
        If not provided, auto-detect by the animal naming scheme.

    """

    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path=None,
                 stim_lib_path=None,
                 block_folder=None,
                 metadata_save_path=None,
                 experiment_type=_DEFAULT_EXPERIMENT_TYPE,
                 legacy_block=None,
                 ):
        self.block_metadata_path = block_metadata_path
        self.metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.block_folder = block_folder
        self.surgeon_initials, self.animal_name, self.block_tag = split_block_folder(block_folder)
        self.metadata_save_path = metadata_save_path
        self.experiment_type = experiment_type
        self.yaml_lib_path = os.path.join(self.metadata_lib_path, self.experiment_type)
        self.__detect_legacy_block(legacy_block)

        if self.metadata_save_path is not None:
            os.makedirs(self.metadata_save_path, exist_ok=True)

        if self.legacy_block:
            self.metadata_reader = LegacyMetadataReader(
                block_metadata_path=self.block_metadata_path,
                metadata_lib_path=self.metadata_lib_path,
                block_folder=self.block_folder,
                metadata_save_path=self.metadata_save_path)
        else:
            self.metadata_reader = MetadataReader(
                block_metadata_path=self.block_metadata_path,
                metadata_lib_path=self.metadata_lib_path,
                block_folder=self.block_folder,
                metadata_save_path=self.metadata_save_path)

    def __detect_legacy_block(self, legacy_block=None):
        if (legacy_block is not None):
            self.legacy_block = legacy_block
            return

        # detect which pipeline is used, based on animal naming scheme
        if self.surgeon_initials is not None:
            self.legacy_block = False
        else:
            self.legacy_block = True

    def extract_metadata(self):
        metadata_input = self.metadata_reader.read()

        metadata = self._extract(metadata_input)

        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_full.yaml',
                       metadata)

        return metadata

    def _extract(self, metadata_input):
        metadata_input['experiment_type'] = self.experiment_type

        metadata = {}
        metadata['block_name'] = self.block_folder

        input_block_name = metadata_input.pop('name', None)
        if (input_block_name is not None) and input_block_name != metadata['block_name']:
            metadata['block_name_in_source'] = input_block_name

        # extract and add metadata fields in this order
        for key in ('experimenter', 'lab', 'institution',
                    'experiment_description', 'session_description',
                    'subject', 'surgery', 'pharmacology', 'notes',
                    'experiment_meta', 'experiment_type',
                    'stimulus', 'extra_meta',
                    'device'
                    ):
            value = metadata_input.pop(key, None)
            if value is None:
                continue
            if key == 'stimulus':
                self.__load_stimulus_info(value)
            if key == 'device':
                self.__load_probes(value)
            metadata[key] = value

        # extract all remaining fields
        for key, value in metadata_input.items():
            logger.info(f'WARNING - unknown metadata field {key}')
            metadata[key] = value

        # final validation
        self.__check_subject(metadata)

        return metadata

    def __check_subject(self, metadata):
        if 'subject' not in metadata:
            metadata['subject'] = {}
        if 'subject_id' not in metadata['subject']:
            metadata['subject']['subject_id'] = self.animal_name
        if 'species' not in metadata['subject']:
            if metadata['subject']['subject_id'][0] == 'R':
                metadata['subject']['species'] = 'Rat'
        for key in ('description', 'genotype', 'sex', 'weight'):
            if key not in metadata['subject']:
                metadata['subject'][key] = 'Unknown'

    def __load_stimulus_info(self, stimulus_metadata):
        if stimulus_metadata['name'] is None:
            # stimulus is not specified for this block
            # let NWBBuilder decide what to do in this case
            logger.warning('Missing stimulus name in metadata.')
            return

        stim_name, _ = check_stimulus_name(stimulus_metadata['name'])
        if stim_name != stimulus_metadata['name']:
            stimulus_metadata['alt_name'] = stimulus_metadata['name']
        stim_yaml_path = os.path.join(self.yaml_lib_path, 'stimulus', stim_name + '.yaml')
        logger.debug(f'Trying to read stimulus metadata from {stim_yaml_path}...')
        stimulus_metadata.update(read_yaml(stim_yaml_path))

    def __load_probes(self, device_metadata):
        e_id_gen = itertools.count()    # Electrode ID, unique for channels across devices
        for key, value in device_metadata.items():
            if key in ('ECoG', 'Poly'):
                if isinstance(value, str):
                    device_metadata[key] = {'name': value}
                dev_conf = device_metadata[key]
                for float_attr in ['resolution', 'conversion']:
                    try:
                        dev_conf[float_attr] = float(dev_conf[float_attr])
                    except KeyError:
                        pass

                probe_path = os.path.join(self.yaml_lib_path, 'probe', dev_conf['name'] + '.yaml')
                dev_conf.update(read_yaml(probe_path))

                # replace ch_ids and ch_pos with a single ch_map (OrderedDict)
                ch_ids = dev_conf.pop('ch_ids')
                ch_pos = dev_conf.pop('ch_pos')
                ch_map = OrderedDict()
                for i in ch_ids:
                    e_id = next(e_id_gen)
                    ch_map[i] = {'electrode_id': e_id,
                                 'x': ch_pos[str(i)]['x'],
                                 'y': ch_pos[str(i)]['y'],
                                 'z': ch_pos[str(i)]['z']}
                dev_conf['ch_map'] = ch_map

                # TODO/CONSIDER: apply offset to all poly ch_pos systematically?
                # (using metadata 'poly_ap_loc' and 'poly_dev_loc')

                # set up device descriptions;
                # prepare two versions for device and e-group
                basic_description = f"{dev_conf.pop('nchannels')}-ch {key}"
                extra_device_description = ""
                if 'serial' in dev_conf:
                    # for new data only
                    extra_device_description += f"serial={dev_conf.pop('serial')}. "
                if 'acq' in dev_conf:
                    acquisition = dev_conf.pop('acq').replace(' ', '-')
                    extra_device_description += f'acq={acquisition}. '
                if 'comment' in dev_conf:
                    extra_device_description += f"{dev_conf.pop('comment')}. "

                # keep poly_neighbors, if applicable, after channel remapping
                poly_neighbors = dev_conf.pop('poly_neighbors', None)
                if poly_neighbors is not None:
                    # apply ch_map, and flatten to a text description
                    location_details = "poly_neighbors=["
                    location_details += (", ".join([str(ch_map[pn]['electrode_id'])
                                                    for pn in poly_neighbors])).rstrip(', ')
                    location_details += "]. "
                else:
                    location_details = ''

                dev_conf['descriptions'] = {} # ignore existing placeholder text
                device_description = (
                    f"{basic_description} from {dev_conf['manufacturer']} "
                    f"({dev_conf.pop('device_type')}). "
                    f"{extra_device_description}"
                    f"n_columns={dev_conf.pop('n_columns')}, "
                    f"n_rows={dev_conf.pop('n_rows')}, "
                    f"orientation={dev_conf.pop('orientation')}, ")
                for sp in ('xspacing', 'yspacing', 'zspacing'):
                    if sp in dev_conf:
                        device_description += f"{sp}={dev_conf.pop(sp)}mm, "
                device_description += f"prefix={dev_conf['prefix']}."
                dev_conf['descriptions']['device_description'] = device_description

                dev_conf['descriptions']['electrode_group_description'] = (
                    f"{basic_description}. "
                    f"{location_details}").strip()

                # add device location if not already specified
                if ('location' not in device_metadata[key] or
                        len(device_metadata[key]['location']) == 0):
                    if self.experiment_type == 'auditory':
                        device_metadata[key]['location'] = 'AUD'

                # drop unused items
                if 'probe_config' in dev_conf:
                    dev_conf.pop('probe_config')
