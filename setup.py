from setuptools import find_packages, setup

# set variable __version__
with open('nsds_lab_to_nwb/version.py') as f:
    exec(f.read())

setup(
    name='nsds_lab_to_nwb',
    version=__version__,
    description=('Convert NSDS Lab data to NWB files.'),
    url='https://github.com/BouchardLab/nsds_lab_to_nwb',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.yaml', '*.conf']}
)
