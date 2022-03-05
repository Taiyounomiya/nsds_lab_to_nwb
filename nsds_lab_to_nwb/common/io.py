import io
import json
import yaml
import csv
import h5py
import scipy.io
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --- yaml ---

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


def write_yaml(yml_path, data, access_mode='w', default_flow_style=False, sort_keys=False):
    # note: additional kwargs may not work in older versions of pyyaml
    # add representer for OrderedDict
    od_representer = (lambda dumper, data:
                      dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
    yaml.add_representer(OrderedDict, od_representer)
    try:
        with io.open(yml_path, access_mode) as fh:
            yaml.dump(data, fh,
                      Dumper=MyDumper,
                      default_flow_style=default_flow_style,
                      sort_keys=sort_keys)
    except PermissionError:
        logger.debug(f'Failed to write yaml due to permissions error in {yml_path}')


def read_yaml(file_path):
    with open(file_path, 'r') as stream:
        content_dict = yaml.safe_load(stream)
        content = json.loads(json.dumps(content_dict))
        return content


# --- csv ---

def csv_to_dict(csv_file):
    with open(csv_file, mode='r') as infile:
        reader = csv.reader(infile)
        mydict = {rows[0]: rows[1] for rows in reader}
    # skip header
    if ('key', 'value') in mydict.items():
        mydict.pop('key')
    return mydict


# --- other file types ---

def read_mat_file(file_path):
    try:
        f = h5py.File(file_path, 'r')
    except OSError:
        # if we get 'OSError: Unable to open file (File signature not found)'
        # this mat file may be from an earlier MATLAB version
        # and is not in HDF5 format.
        f = scipy.io.loadmat(file_path)
    return f
