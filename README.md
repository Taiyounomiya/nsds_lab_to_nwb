# NSDS-Lab-to-NWB

Python code package to convert NSDS lab data to NWB files.

<!--
Under development - anything could change.

Metadata library is in a separate repository [NSDSLab-NWB-metadata](https://github.com/BouchardLab/NSDSLab-NWB-metadata) (private to BouchardLab).
-->


## Setup

### Prerequisite

Make sure that you have conda (either anaconda or miniconda) installed.


### Installing this package

Clone this repository and `cd` to the repository root:

```bash
cd [your_project_folder]
git clone git@github.com:BouchardLab/nsds_lab_to_nwb.git
cd nsds_lab_to_nwb
```

Create a conda environment (named `nsds_nwb` by default), and activate it:

```bash
conda env create -f environment.yml
conda activate nsds_nwb
```

Also install this package:

```bash
pip install -e .
```

### Setting the default paths

It is recommended to set the default data, metadata and stimulus paths
as the environment variables.

If you are running this on catscan, open your `~/.bashrc` file in any text editor,
and copy and paste the following lines into the `~/.bashrc` file.

```bash
export NSDS_METADATA_PATH='/clusterfs/NSDS_data/NSDSLab-NWB-metadata/'
export NSDS_DATA_PATH='/clusterfs/NSDS_data/raw/'
export NSDS_STIMULI_PATH='/clusterfs/NSDS_data/stimuli/'
```

After you edit the `~/.bashrc` file, run

```bash
source ~/.bashrc
```

for the change to take effect.


If you are not on catscan, you should make sure that the values of the three environment variables are set correctly, such that the software can find the data, metadata and stimulus files.
You will need to clone the [NSDSLab-NWB-metadata repository](https://github.com/BouchardLab/NSDSLab-NWB-metadata) and make sure that `NSDS_METADATA_PATH` points to the repository.

<!--
```bash
mkdir -p ~/Src
cd ~/Src
git clone git@github.com:BouchardLab/NSDSLab-NWB-metadata.git
```
-->

Also see the [Naming Conventions documentation](https://nsds-lab-to-nwb.readthedocs.io/en/latest/naming_conventions.html) for more information.
