from pynwb import NWBHDF5IO
import argparse

parser = argparse.ArgumentParser(description='Print NWB details',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('file', type=str, help='NWB file')
parser.add_argument('--acq', type=str, default=None,
                    help='Prints details from a acquisition dataset if specified')
parser.add_argument('--prep', type=str, default=None,
                    help='Prints details from a preprocessing dataset if specified. ' +
                    'If not found, prints list of datasets')
parser.add_argument('--trials', action='store_true',
                    help='Prints first 5 trials from trials table')
args = parser.parse_args()
nwb_file = args.file
acq = args.acq
prep = args.prep
trials = args.trials

f = NWBHDF5IO(nwb_file, mode='r')
contents = f.read()
print(contents)

if acq is not None:
    acq_contents = contents.acquisition[acq]
    print(acq_contents)

if prep is not None:
    try:
        prep_contents = contents.processing['preprocessing'][prep]
    except KeyError:
        prep_contents = contents.processing['preprocessing']
        print(f'{prep} does not exist. Here is a list of datasets in the preprocessing module: ')
    print(prep_contents)
if trials:
    print(contents.trials.to_dataframe().head())
