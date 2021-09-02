import os
import warnings

import numpy as np

from .htkfile import HTKFile

"""
Module used for reading of collections of HTK files of raw or processed neural recordings.

"""

"""
This file is originally based on sources available in BRAINformat. The file has been
modified to meet NWB needs.


BRAINFormat Copyright (c) 2014, 2015, The Regents of the University of California, through
Lawrence Berkeley National Laboratory (subject to receipt of any required approvals
from the U.S. Dept. of Energy).  All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

(1) Redistributions of source code must retain the above copyright notice, this list
    of conditions and the following disclaimer.

(2) Redistributions in binary form must reproduce the above copyright notice, this
    list of conditions and the following disclaimer in the documentation and/or
    other materials provided with the distribution.

(3) Neither the name of the University of California, Lawrence Berkeley National
    Laboratory, U.S. Dept. of Energy nor the names of its contributors may be
    used to endorse or promote products derived from this software without specific
    prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.

You are under no obligation whatsoever to provide any bug fixes, patches, or upgrades
to the features, functionality or performance of the source code ("Enhancements")
to anyone; however, if you choose to make your Enhancements available either publicly,
or directly to Lawrence Berkeley National Laboratory, without imposing a separate
written license agreement for such Enhancements, then you hereby grant the following
license: a  non-exclusive, royalty-free perpetual license to install, use, modify,
prepare derivative works, incorporate into other computer software, distribute, and
sublicense such enhancements or derivative works thereof, in binary and source code form.
"""


class HTKCollection(object):
    """
    Class for management of a directory of HTK files from raw or processed neural recordings.
    All HTK files are expected to have the same size.

    :ivar directory: Directory where the raw HTK data files are located
    :ivar htk_files: Python list of strings of the paths to all HTK files
    :ivar channel_to_file_map: 2D numpy array of shape (#blocks, #channels) indicating the
          index of the file associated with the corresponding channel.
    :ivar file_to_channel_map: List of two-valued tuples indicating for each file the
            block and channel they are associated with. blockindex=self.file_to_channel_map[i][0].
    :ivar data: 2D numpy array with the full data from all channels of None in case read_data() has not been called.
    :ivar layout: Numpy array describing the physical layout of the grid. By default a rectangular layout is assumed
            with channels starting at the bottom right of the grid and channel numbers growing from bottom to top.
    :ivar num_samples: Number of samples per channel
    :ivar sample_period: Sample period in 100ns units
    :ivar sample_rate: Sampling rate in Hz. This is the same as 10000/sample_period.
    :ivar sample_size: Number of bytes per sample
    :ivar parameter_kind: Code indicating the sample kind (see HTKFormat for details on parmKind)
    :ivar anatomy: Dictionary describing for different regions of the brain the electrodes that are located in
                   the given region.
    :ivar dtype: Numpy dtype of the HTK data
    :ivar sample_rate_base: None if the sample_period is given in the header. Set to the number that
            should we should divide the sampling rate given in the header by in order to convert the
            rate to the appropriate value in Hz.
    :var bands: 1D numpy array with center of the frequency bands
    """
    def __init__(self,
                 directory,
                 prefix=None,
                 layout=None,
                 anatomy_file=None,
                 bands_file=None,
                 guess_bands=False,
                 check_consistency=False,
                 sample_rate_base=10000.,
                 noblock=True,
                 postfix=None):
        """
        Initialize object for management of directory of RAW neural recording in HTK format.

        NOTE: The original HTK specification specifies that the sample_period is given in the header in 100ns
        units. In some cases however, users appear to write the sampling rate in the header with a different
        base. We therefore allow users to specify the base for the sampling rate and if given we assume that
        the header contains the sampling rate and we convert accordingly.

        :param directory: Directory with the raw HTK files
        :param prefix: Optional prefix value valid HTK files must have.
        :param layout: Array defining the layout of the electrodes. Set to None to use the default layout
                      of m x m computed using the get_layout function. E.g., the default layout for 16
                      electrodes is a 4x4 grid array with origin being located in the bottom right corner:
                      ([[15, 11,  7,  3], [14, 10,  6,  2], [13,  9,  5,  1], [12,  8,  4,  0]])
        :param anatomy_file: Optional file describing the anatomy of the electrodes (.mat file)
        :param bands_file: Optional file describing the center of the frequency bands in the neural recordings:
        :type bands_file: String indicating the name of the .mat Matlab file.
        :param guess_bands: If no bands file is given, should we guess the bands from the file-name.
        :type guess_bands: Boolean
        :param check_consistency: Check that all HTK files in the collection have the same structure.
        :type check_consistency: Boolean
        :param sample_rate_base: None if the sample_period is given in the header. Set to the number that
            should we should divide the sampling rate given in the header by in order to convert the
            rate to the appropriate value in Hz.
        :param noblock: Boolean to indicate that no block index is given in the filename (default=True)
        :type noblock: bool
        :param postfix: Tuple of valid postfix strings values or numpy array of ints with the file index values

        :raises: AssertionError is raised if check_consistency if enabled and inconsistencies
                 in metadata are found between HTK files in the collection.

        """
        self.sample_rate_base = sample_rate_base
        self.directory = os.path.abspath(directory)
        self.prefix = prefix
        self.noblock = noblock
        self.postfix = postfix if postfix is None else postfix
        self.htk_files, self.channel_to_file_map, self.file_to_channel_map = self.__get_htk_files()
        self.data = None
        (self.num_samples, self.sample_period, self.sample_rate, self.sample_size,
         self.parameter_kind, self.num_bands, self.dtype) = self.__get_htk_metadata()
        if check_consistency:
            assert self.__check_consistency()
        if layout is None:
            self.layout = self.get_layout(len(self.htk_files))
        else:
            self.layout = layout
        if anatomy_file:
            self.anatomy = self.read_anatomy(anatomy_file)
        else:
            self.anatomy = {}
        self.bands = self.__get_bands(bands_file=bands_file,
                                      guess_bands=guess_bands)
        self.shape = (int(len(self.htk_files)), int(self.num_samples), int(self.num_bands))

    def __get_bands(self, bands_file=None, guess_bands=False):
        """
        Try to construct the bands from the filename. Note, this assumes that the metadata has already been
        constructed.

        :param bands_file: Matlab file with the frequency bands. If not present, then the function will try
                          to construct the frequency bands based on the filename.
        :param guess_bands: If no bands file is given, should we guess the bands from the file-name.

        """
        # Default is the bands are just numbered from 0 to #bands
        bands = None
        # Compute the bands
        if bands_file is None:
            # The user provided us with a list of bands
            if isinstance(guess_bands, list):
                bands = guess_bands
            # Try to construct the bands from the filename
            elif guess_bands:
                # The filename is expected to be of the form *_70to150_8band
                basename = os.path.basename(self.directory)
                if len(basename) == 0:
                    basename = os.path.basename(os.path.split(self.directory)[0])
                band_index = basename.find('band')
                if band_index > 0:
                    basename = basename[0:band_index]
                    splitname = basename.split('_')
                    if splitname[-1].isdigit():
                        filename_num_bands = int(splitname[-1])
                    else:
                        filename_num_bands = None
                    if filename_num_bands != self.num_bands:
                        warnings.warn(('Number of bands in the directory name %i'
                                       'does not match number of bands in files %i.')
                                      % (filename_num_bands, self.num_bands))
                    rangestr = splitname[-2].split('to')
                    if len(rangestr) == 2:
                        if rangestr[0].isdigit() and rangestr[1].isdigit():
                            low_frequency = int(rangestr[0])
                            high_frequency = int(rangestr[1])
                            frequency_range = high_frequency - low_frequency
                            # Linear band stepping
                            # step = (high_frequency-low_frequency) / float(self.num_bands)
                            # bands = np.hstack((np.arange(low_frequency, high_frequency, step), high_frequency))
                            # Logarithmic band centers
                            bands = np.logspace(start=0,
                                                stop=np.log10(frequency_range),
                                                num=self.num_bands,
                                                endpoint=False)
                            bands += low_frequency
        # Read the bands from the Matlab file
        elif bands_file is not None:
            import scipy.io as sio
            bandmat = sio.loadmat(bands_file)
            for i in bandmat.keys():
                if i not in ['__version__', '__globals__', '__header__']:
                    bandkey = i
                    break
            else:
                raise KeyError("Could not determine the bands dataset from the bands_file")
            banddat = bandmat[bandkey]
            bands = banddat.reshape(banddat.size)

        return bands

    @staticmethod
    def read_anatomy(anatomy_file):
        """
        Read .mat file describing the anatomy of the data and return a dict
        describing for different brain regions (keys) the set of electrodes
        that are located in that region (values, stored as numpy arrays).

        :param anatomy_file: The name of the .mat file with the description of the anatomy
        """
        import scipy.io as sio
        anatomy_mat = sio.loadmat(anatomy_file)             # Load the .mat file
        region_names = anatomy_mat['anatomy'].dtype.names   # Get all name keys for the regions
        region_selection = anatomy_mat['anatomy'][0][0]     # Get the dataset with the region selections
        num_regions = len(region_names)                     # Number of regions
        # Compute the dict describing the regions and convert to 0-based index
        anatomy_dict = {region_names[i]: (region_selection[i].flatten() - 1) for i in range(num_regions)}
        return anatomy_dict

    @staticmethod
    def get_layout(num_electrodes):
        """
        Internal helper function used to define the default layout of the brain grid.

        :param num_electrodes: The number of electrodes to be arranged in the layout
        """
        import math
        grid_size = int(math.sqrt(num_electrodes))
        if (grid_size * grid_size) != num_electrodes:
            warnings.warn('Default rectangular layout not possible for given HTK collection.')
            return None
        # Create a n x n matrix and roll the axis to get the numbers to be ordered in the columns and then
        # flip left-right and flip up-down to make sure the array is order. E.g., for a 4x4 grid for ordering
        # 16 channels the layout would be:
        #   np.fliplr(np.flipud(np.rollaxis(np.arange(16).reshape((4,4)),1)))
        #    array([[15, 11,  7,  3],
        #           [14, 10,  6,  2],
        #           [13,  9,  5,  1],
        #           [12,  8,  4,  0]])
        return np.fliplr(np.flipud(np.rollaxis(np.arange(num_electrodes).reshape((grid_size, grid_size)), 1)))

    def __get_htk_metadata(self):
        """
        Internal helper function used to retrieve the sampling rate, number of samples
        sample size, and parameter kind.
        NOTE! This function assumes that the list of htk_files has already been computed.
        """
        if len(self.htk_files) > 0:
            tempfile = HTKFile(self.htk_files[0], sample_rate_base=self.sample_rate_base)
            num_samples = tempfile.num_samples
            sample_period = tempfile.sample_period
            sample_rate = tempfile.sample_rate
            sample_size = tempfile.sample_size
            parameter_kind = tempfile.parameter_kind
            num_bands = tempfile.vector_length
            dtype = tempfile.read_sample(0).dtype
            del tempfile
            return num_samples, sample_period, sample_rate, sample_size, parameter_kind, num_bands, dtype

    def __check_consistency(self):
        """
        Internal helper function used to check that all HTK files in the collection
        have the same structure (i.e, whether the header information of the HTK files
        is the same for all files).
        NOTE! This function assumes that the list of htk_files has already been computed.
        """
        if len(self.htk_files) <= 1:
            return True
        else:
            consistent = True
            tempfile = HTKFile(self.htk_files[0], sample_rate_base=self.sample_rate_base)
            num_samples1 = tempfile.num_samples
            sample_period1 = tempfile.sample_period
            sample_rate1 = tempfile.sample_rate
            sample_size1 = tempfile.sample_size
            parameter_kind1 = tempfile.parameter_kind
            del tempfile
            for filename in self.htk_files:
                tempfile = HTKFile(filename, sample_rate_base=self.sample_rate_base)
                num_samples2 = tempfile.num_samples
                sample_period2 = tempfile.sample_period
                sample_rate2 = tempfile.sample_rate
                sample_size2 = tempfile.sample_size
                parameter_kind2 = tempfile.parameter_kind
                consistent &= num_samples1 != num_samples2 or \
                    sample_period1 != sample_period2 or \
                    sample_rate1 != sample_rate2 or \
                    sample_size1 != sample_size2 or \
                    parameter_kind1 != parameter_kind2
                del tempfile
                if not consistent:
                    break
            return consistent

    def __get_htk_files(self):
        """
        Internal helper function used to compute the list of files
        (stored in self.htk_files) and the map of files to channels/blocks
        (stored in self.channel_block_map).

        :returns: This function returns: i) a list of htk filenames,
                  ii) a 2D numpy array of shape (#blocks, #channels)
                  indicating the index of the file associated with
                  a given channel, and iii) a list of tuples indicating
                  for each file the block and channel index.

        :raises: A ValueError is raised in case that HTK files of varying sizes are found.

        """
        # Compute the list of all htk files
        filelist = [os.path.join(self.directory, filename)      # Record the full path off all htk files
                    for filename in os.listdir(self.directory)  # Iterate through all files in the directory
                    if filename.endswith('.htk')]               # Record all HTK files
        # print(filelist)
        if self.prefix is not None: # Remove all files from the list that do not have the approbriate prefix
            filelist = [filename for filename in filelist if os.path.basename(filename).startswith(self.prefix)]
            # print([os.path.basename(filename) for filename in filelist])
        if isinstance(self.postfix, tuple):  # Remove all files that do not have a given postfix
            filelist = [filename for filename in filelist if filename[:-4].endswith(self.postfix)]
            print(filelist)
        if isinstance(self.postfix, np.ndarray):
            temp_list = []
            for filename in filelist:
                bi, ci = self.__get_block_channel_index_from_name(filename, self.noblock)
                if self.noblock:
                    if ci in self.postfix:
                        temp_list.append(filename)
                else:
                    if int(str(bi) + str(ci)) in self.postfix:
                        temp_list.append(filename)
            filelist = temp_list

        # Check if we have any files and warn the user if the folder did not contain any valid HTK files
        if len(filelist) == 0:
            warnings.warn('No HTK files found in the given data directory.')
            return [], np.zeros((0, 0), dtype='uint64'), []
        # Check if all files in the list have the same size
        filesizes = np.asarray([os.path.getsize(path) for path in filelist])
        if len(np.unique(filesizes)) != 1:
            raise ValueError('HTK files of varying size found in the same location. Try to set the prefix filter')

        # Compute based on the filename the block and channel index
        blockindex = [-1] * len(filelist)
        channelindex = [-1] * len(filelist)
        for fileindex, filepath in enumerate(filelist):
            blockindex[fileindex], channelindex[fileindex] = self.__get_block_channel_index_from_name(filepath,
                                                                                                      self.noblock)
        blockindex = np.asarray(blockindex)
        channelindex = np.asarray(channelindex)
        numblocks = blockindex.max()
        numchannels = channelindex.max()
        blockindex -= 1  # In the file name encoding block indicies are 1 based
        channelindex -= 1  # In the file name encoding channel indicies are 1 based
        if channelindex.min() > 0:
            numchannels = len(filelist)
            channelindex -= channelindex.min()

        # Sort the files based on their block and channel index
        filelist, blockindex, channelindex = self.__sort_files(filelist=filelist,
                                                               blockindex=blockindex,
                                                               channelindex=channelindex,
                                                               numchannels=numchannels)
        # Compute the channel+block to file map
        cbmap = np.zeros(shape=(numblocks, numchannels), dtype='uint64')
        for fileindex in range(len(filelist)):
            cbmap[blockindex[fileindex], channelindex[fileindex]] = fileindex

        # Compute the file to block+channel map
        fmap = list(zip(blockindex, channelindex))

        # Return the filelist and maps
        return filelist, cbmap, fmap

    @staticmethod
    def __sort_files(filelist, blockindex, channelindex, numchannels):
        """
        Based on the blockindex and channelindex of the files,
        compute the linear order in which the files should be sorted.

        :param filelist: List of all files
        :param blockindex: Numpy array with the block index for each file.
        :param channelindex: Numpy array with the channel index within each block for each file.
                             channelindex must be the same length as blockindex
        :param numchannels: Number of channels per block (usually channelindex.max())
        """
        # Compute the sorting index for the files
        fileorder = np.zeros(shape=(len(filelist)), dtype='uint64')
        for fileindex, location in enumerate(zip(blockindex, channelindex)):
            # Compute the index of the file in the 2D array
            targetindex = location[0] * numchannels + location[1]
            fileorder[targetindex] = fileindex

        # Reorder the filelist, blocklist and channel list
        outfilelist = [filelist[i] for i in fileorder]
        outblockindex = blockindex[fileorder]
        outchannelindex = channelindex[fileorder]

        # Return the sorted files, blockindex, and channelindex
        return outfilelist, outblockindex, outchannelindex

    @staticmethod
    def __get_block_channel_index_from_name(filename, noblock=False):
        """
        Internal helper function used to determine the block index
        and channel index based on the name of the file.

        :param filename: Name of the HTK file
        :type filename: string
        :param noblock: Boolean to indicate that no block index is given in the filename (default=False)
        :type noblock: bool

        :returns: Integer of the block index and integer of the channel index within the block
        """
        basename = os.path.basename(filename).rstrip('.htk')
        # Get all digits at the end of the filename
        indexstring = ""
        for endchar in reversed(basename):
            if endchar.isdigit():
                indexstring = endchar + indexstring
            else:
                break
        # Calculate the block and channel index from the string
        if noblock:
            channelindex = int(indexstring)
            blockindex = 1
        else:
            blockindex = int(indexstring[0])
            channelindex = int(indexstring[1:])
        # Retrun the block and channelindex
        return blockindex, channelindex

    def get_anatomy_dict(self):
        """
        Get the anatomy dicitionary describing for each region
        the list of electrodes in the region.
        """
        return self.anatomy

    @staticmethod
    def get_anatomy_map(anatomy_dict, num_electrodes):
        """
        Get numpy array of string, indicating for each electrode the
        name of the region it is located in . 'unknown' is added
        for electrodes with an unknown region assignment.
        """
        num_files = num_electrodes
        # Determine the string dtype to be uses based on the length of the strings
        an_dtype = np.asarray(list(anatomy_dict.keys())).dtype
        if np.dtype(an_dtype).itemsize < 7:
            an_dtype = np.dtype('|S7')  # S7 needed for unknown
        # Initialize the map as all unknown
        anatomy_map = np.asarray(['unknown' for _ in range(num_files)],
                                 dtype=an_dtype)
        # Assign the region names to all channels for which they are giben
        for region_name, region_select in anatomy_dict.items():
            anatomy_map[region_select] = region_name
        return np.asarray(anatomy_map)

    def has_anatomy(self):
        """
        Check whether anatomy data is available for the collection.
        """
        return len(self.anatomy) > 0

    def get_block_index(self, fileindex):
        """
        Get the block index for the file with the given index.

        :param fileindex: Index of the file of interest

        :returns: integer indicting the block index for the file.
        """
        return self.file_to_channel_map[fileindex][0]

    def get_channel_index(self, fileindex):
        """
        Get the channel index with a block for the file with the given index.

        :param fileindex: Index of the file of interest

        :returns: integer indicting the channel index for the file.
        """
        return self.file_to_channel_map[fileindex][1]

    def get_number_of_files(self):
        """
        Get the number of HTK files associated with the current collection of raw data.

        :returns: Integer indicating the number of HTK files. (len(self.htk_files))
        """
        return len(self.htk_files)

    def get_number_of_blocks(self):
        """
        Get the number of blocks in which the all channels are organized.
        """
        return self.channel_to_file_map.shape[0]

    def get_number_of_channels_per_block(self):
        """
        Get the number of channels per block.
        """
        return self.channel_to_file_map.shape[1]

    def clear_data(self):
        """
        Clear the self.data instance variable to free up memory.
        """
        del self.data
        self.data = None

    def read_channel(self, fileindex):
        """
        Get the data for the file with the given index.
        """
        if self.data:
            return self.data[fileindex]
        else:
            tempfile = HTKFile(self.htk_files[fileindex], sample_rate_base=self.sample_rate_base)
            return tempfile.read_data()

    def read_data(self, print_status=False):
        """
        Read all data from file and return the numpy array.
        This function modifies self.data to safe the data
        retrieved.

        :param print_status: One of [True, False, 'jupyter']. True means-Print status message on
                        read progress on screen. 'jupyter' means create a progress bar in a Jupyter notebook.
                        False means, don't show process. Default is False.
        """
        if print_status is True:
            import sys
        elif print_status == 'jupyter':
            from bouchardlab.misc.widgets import log_progress

        # Read the data from file if we have not done so before
        if self.data is None:
            # Read all HTK data files in order of appearance in the map
            # datalist = [None]*len(self.htk_files)
            self.data = np.zeros(shape=self.shape, dtype=self.dtype)
            loop_var = enumerate(self.htk_files)
            if print_status == 'jupyter':
                loop_var = log_progress(loop_var, every=1, size=len(self.htk_files),
                                        name=(os.path.basename(self.directory) + ' Channels'))
            for fileindex, filename in loop_var:
                if print_status is True:
                    sys.stdout.write("Reading HTK Collection: [" +
                                     str(int(100. * float(fileindex) / float(len(self.htk_files) - 1))) +
                                     "%]" + "\r")
                    sys.stdout.flush()
                tempfile = HTKFile(filename, sample_rate_base=self.sample_rate_base)
                # datalist[fileindex] = tempfile.read_data()
                self.data[fileindex] = tempfile.read_data()
                del tempfile
            if print_status:
                print('')
            # Convert the data to numpy and make sure we have a 2D shaped array if we only have one frequency band
            # self.data = np.asarray(datalist)
        # Return the full data
        return self.data


try:
    # from form.data_utils import DataChunkIterator, DataChunk
    from hdmf.data_utils import AbstractDataChunkIterator, DataChunk
    from hdmf.utils import docval, getargs

    class HTKChannelIterator(AbstractDataChunkIterator):
        """
        Custom data chunk iterator to iterate over the channels of an HTK collection.
        """
        # @docval({'name': 'data', 'type': HTKCollection, 'doc': 'The HTKCollection to iterate over.'})
        def __init__(self, **kwargs):
            super(HTKChannelIterator, self).__init__()
            self.data = getargs('data', kwargs)
            self.__dtype = getargs('dtype', kwargs)
            self.current_fileindex = 0
            self.time_axis_first = getargs('time_axis_first', kwargs)
            self.__maxshape = list(getargs('maxshape', kwargs))
            self.__has_bands = getargs('has_bands', kwargs)
            if self.time_axis_first:
                # Swap the axes on the shape and maxshape
                self.shape = (self.data.shape[1], self.data.shape[0], self.data.shape[2])
                self.__maxshape[0], self.__maxshape[1] = self.__maxshape[1], self.__maxshape[0]
                self.__maxshape = tuple(self.__maxshape)
                if not self.__has_bands:
                    self.shape = self.shape[0:2]
                    self.__maxshape = self.__maxshape[0:2]

            else:
                self.shape = self.data.shape

        @classmethod
        def from_htk_collection(cls, collection, time_axis_first=False, has_bands=True):
            """
            Convenience function to generate a HTKChannelIterator from an existing HTKCollection
            :param collection: The input HTKCollection for which we should create an iterator
            :type collection: HTKCollection
            :return: HTKChannelIterator for the input HTKCollection
            """
            return cls(data=collection,
                       maxshape=collection.shape,
                       dtype=collection.dtype,
                       time_axis_first=time_axis_first,
                       has_bands=has_bands)

        @property
        def maxshape(self):
            return self.__maxshape

        @property
        def dtype(self):
            return self.__dtype

        def __iter__(self):
            """Return the iterator object"""
            return self

        def __next__(self):
            """Return the next data chunk or raise a StopIteration exception if all chunks have been retrieved."""
            next_chunk = []
            # Determine the range of channels to be read
            start_index = self.current_fileindex
            stop_index = start_index + 1  # self.buffer_size
            if stop_index > self.data.get_number_of_files():
                stop_index = self.data.get_number_of_files()
            # Read the data from all current channels
            for i in range(start_index, stop_index):
                next_chunk.append(self.data.read_channel(i))  # Read a single HTK file with the data of one electrode
            next_chunk_size = len(next_chunk)
            # If didn't read any channels then return None, None
            if next_chunk_size == 0:
                raise StopIteration
            # If we had data, then determine the chunk location and convert the data to numpy, and return
            else:
                self.current_fileindex = stop_index
                next_chunk = np.asarray(next_chunk)
                if self.time_axis_first:
                    next_chunk = np.swapaxes(next_chunk, 0, 1)
                else:
                    next_chunk_location = np.s_[start_index:stop_index, ...]

                if self.__has_bands:
                    next_chunk_location = np.s_[:, start_index:stop_index, :]
                else:
                    next_chunk_location = np.s_[:, start_index:stop_index]
                    next_chunk = next_chunk[:, :, 0]
                # print(next_chunk.shape, next_chunk_location)
                return DataChunk(next_chunk, next_chunk_location)

        @docval(returns='Tuple with the recommended chunk shape or None if no particular shape is recommended.')
        def recommended_chunk_shape(self):
            """Recommend a chunk shape. This will typcially be the most common shape of chunk returned by __next__
            but may also be some other value in case one wants to recommend chunk shapes to optimize read rather
            than write."""
            None

        def recommended_data_shape(self):
            """Recommend an initial shape of the data. This is useful when progressively writing data and
            we want to recommend and initial size for the dataset"""
            if self.__maxshape is not None:
                if np.all([i is not None for i in self.__maxshape]):
                    return self.__maxshape
            return self.__first_chunk_shape

except ImportError:
    warnings.warn("Could not import hdmf.utils.DataChunkIterator. HTKChannelIterator not available")
