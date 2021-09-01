import numpy as np
from .htkcollection import HTKCollection, HTKChannelIterator
# try:
#    from scipy.misc import imread
# except ImportError:
#     from scipy.ndimage import imread
from imageio import imread
from copy import deepcopy

"""
Instrument metadata related classes and functions
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


class EPhysInstrumentData:
    """
    Describe the data for a particular recording device
    """
    def __init__(self,
                 htkdir,
                 prefix,
                 postfix,
                 device_name=None,
                 device_image_name=None,
                 description=None,
                 layout=None,
                 location=None,
                 read_on_create=True,
                 **kwargs):
        """
        Store information about how to read the data for the instrument

        :param htkdir: Directory where the HTK files are located
        :param postfix: Numpy array with the postfix values for the HTK files with the recording channels
        :param device_name: String indicating the type of recording device used
        :param device_image_name: String to the path of the image of device (default=None)
        :param description: String wiht additional descripitn of the device (default=None)
        :param layout: Numpy array with the layout of the electrodes, e.g., computed via InstrumentLayout.grid
                       or InstrumentLayout.polytrode
        :param location: Optional array describing the location of the device
        :param read_on_create: Bool indicating whether we should call read_data(...) to read all the data when
                                calling the constructor. If set to False then we need to call read_data later
                                if we need to access the data.
        :param kwargs: Dict with additional keyword arguments to be passed to HTKCollection
        """
        self.htkdir = htkdir
        self.prefix = prefix
        self.postfix = postfix
        self.device_name = device_name
        self.device_image = None
        self.device_image_name = device_image_name
        self.description = description
        self.layout = layout
        self.location = location
        self.htkcollection_kwargs = deepcopy(kwargs)
        self.bands = None
        self.sample_rate = None
        self.data = None
        if read_on_create:
            self.read_data()

    def read_data(self, create_iterator=False, print_status=False, time_axis_first=True, has_bands=True):
        """
        Read the data for all channels

        :param create_iterator: If set to True, then instead of reading the HTK data we create
                         a HTKChannelIterator object that we can use to iteratively read the
                         channels when we need them
        :param time_axis_first: If set to True, use the dimension order (time, electrode, band)
                         if False use the default ordering (electrode, time, band)
        :param print_status: One of [True, False, 'jupyter']. True means-Print status message on
                        read progress on screen. 'jupyter' means create a progress bar in a Jupyter notebook.
                        False means, don't show process. Default is False.

        :return:
        """
        collection = HTKCollection(self.htkdir,
                                   postfix=self.postfix,
                                   prefix=self.prefix,
                                   layout=self.layout,
                                   **self.htkcollection_kwargs)
        if create_iterator:
            # from mars.io.readers.htkcollection import HTKChannelIterator
            self.data = HTKChannelIterator.from_htk_collection(collection=collection,
                                                               time_axis_first=time_axis_first,
                                                               has_bands=has_bands)
        else:
            self.data = collection.read_data(print_status=print_status)
            if time_axis_first:
                self.data = np.swapaxes(self.data, 0, 1)
        self.sample_rate = collection.sample_rate
        self.bands = collection.bands
        if self.device_image_name is not None:
            self.device_image = imread(self.device_image_name)


class EPhysInstrumentLayout(object):
    """
    Define the layout for different EPhys Instrument
    """

    @staticmethod
    def polytrode(ncols=2):
        """
        Get the layout for the polytrode

        :param ncols: Integer indicating the number of columns in the polytrode. One of 2,3.
        :return:
         * array with the layout index for the polytrode
         * array with the positions of the electrodes or None
        """
        if ncols == 3:
            matlab_array = np.asarray([[np.nan, 17, np.nan],
                                       [10, 16, 23],
                                       [9, 18, 24],
                                       [8, 15, 25],
                                       [7, 19, 26],
                                       [6, 14, 27],
                                       [5, 20, 28],
                                       [4, 13, 29],
                                       [3, 21, 30],
                                       [2, 12, 31],
                                       [1, 22, 32],
                                       [np.nan, 11, np.nan],
                                       ])
        elif ncols == 2:
            matlab_array = np.asarray([[20, 18],
                                       [16, 14],
                                       [12, 10],
                                       [8, 6],
                                       [4, 2],
                                       [22, 24],
                                       [26, 28],
                                       [30, 32],
                                       [31, 29],
                                       [27, 25],
                                       [23, 21],
                                       [1, 3],
                                       [5, 7],
                                       [9, 11],
                                       [13, 15],
                                       [17, 19],
                                       ])
        else:
            raise ValueError("Ncols must be one of 2 or 3")
        python_array = matlab_array - 1
        position_array = None
        return python_array, position_array

    @staticmethod
    def polytrode_position_in_grid(orientiation, xspacing=0.2, yspacing=0.2):
        """
        The location of the polytrode with respect to the ephys grid

        :param orientiation: Char with the channel orientation of the ephys grid. One of 'S' or 'R'
        :param xspacing: Spacing of the electrodes in x
        :param yspacing: Spacing of the electrodes in y

        :return: Two numpy arrays of two floats. The first array is the (x,y) index location in the grid, and the
                 second array is the spatial (x,y) location is the spatial location.
        """
        index_location = np.asarray([7, 0.5])
        spatial_location = np.asarray([index_location[0] * yspacing, index_location[1] * xspacing])
        return index_location, spatial_location

    @staticmethod
    def grid(orientation, nelect=64, xspacing=0.2, yspacing=0.2):
        """

        :param orientation: Char with the channel orientation. One of 'S' or 'R'
        :param nelect: Number of electrodes in the grid
        :param xspacing: The spacing to be used to compute the electrodes x positions
        :param yspacing: The spacing to be used to compute the electrodes y positions
        :return:
            * array with the layout index for the polytrode
            * array with the positions of the electrodes or None
        """
        if nelect == 64:
            # Grid index
            matlab_array = np.asarray([[15, 13, 11, 9, 7, 5, 3, 1],
                                       [16, 14, 12, 10, 8, 6, 4, 2],
                                       [32, 30, 28, 26, 24, 22, 20, 18],
                                       [31, 29, 27, 25, 23, 21, 19, 17],
                                       [47, 45, 43, 41, 39, 37, 35, 33],
                                       [48, 46, 44, 42, 40, 38, 36, 34],
                                       [64, 62, 60, 58, 56, 54, 52, 50],
                                       [63, 61, 59, 57, 55, 53, 51, 49]])
            if orientation == 'R':
                pass
            elif orientation == 'S':
                matlab_array = matlab_array[:, ::-1]
            python_array = matlab_array - 1

            # Grid position
            position_array = np.zeros(shape=(8, 8, 2), dtype='float')
            for i in range(8):
                position_array[i, :, 0] = np.arange(0, 8) * yspacing
                position_array[:, i, 1] = np.arange(0, 8) * xspacing
        elif nelect == 128:
            matlab_array = np.asarray([[47, 48, 64, 63, 65, 66, 82, 81],
                                       [45, 46, 62, 61, 67, 68, 84, 83],
                                       [43, 44, 60, 59, 69, 70, 86, 85],
                                       [41, 42, 58, 57, 71, 72, 88, 87],
                                       [39, 40, 56, 55, 73, 74, 90, 89],
                                       [37, 38, 54, 53, 75, 76, 92, 91],
                                       [35, 36, 52, 51, 77, 78, 94, 93],
                                       [33, 34, 50, 49, 79, 80, 96, 95],
                                       [31, 29, 27, 25, 103, 101, 99, 97],
                                       [23, 21, 19, 17, 111, 109, 107, 105],
                                       [32, 30, 28, 26, 104, 102, 100, 98],
                                       [24, 22, 20, 18, 112, 110, 108, 106],
                                       [16, 14, 12, 10, 120, 118, 116, 114],
                                       [8, 6, 4, 2, 128, 126, 124, 122],
                                       [15, 13, 11, 9, 119, 117, 115, 113],
                                       [7, 5, 3, 1, 127, 125, 123, 121]])
            if orientation == 'R':
                pass
            elif orientation == 'S':
                matlab_array = matlab_array[:, ::-1]
            python_array = matlab_array - 1

            # Grid position
            position_array = np.zeros(shape=(16, 8, 2), dtype='float')
            for i in range(16):
                position_array[i, :, 0] = np.arange(0, 8) * yspacing
            for i in range(8):
                position_array[:, i, 1] = np.arange(0, 16) * xspacing

        else:
            raise ValueError('nelect must be one of [64, 128]')

        return python_array, position_array
