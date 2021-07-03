'''
Defines the header class used for reading, writing and tracking the metadata in the header of a .c3d file.
'''
import sys
import struct
import numpy as np
from .utils import UNPACK_FLOAT_IEEE, DEC_to_IEEE

class Header(object):
    '''Header information from a C3D file.

    Attributes
    ----------
    event_block : int
        Index of the 512-byte block where labels (metadata) are found.
    parameter_block : int
        Index of the 512-byte block where parameters (metadata) are found.
    data_block : int
        Index of the 512-byte block where data starts.
    point_count : int
        Number of motion capture channels recorded in this file.
    analog_count : int
        Number of analog values recorded per frame of 3D point data.
    first_frame : int
        Index of the first frame of data.
    last_frame : int
        Index of the last frame of data.
    analog_per_frame : int
        Number of analog frames per frame of 3D point data. The analog frame
        rate (ANALOG:RATE) is equivalent to the point frame rate (POINT:RATE)
        times the analog per frame value.
    frame_rate : float
        The frame rate of the recording, in frames per second.
    scale_factor : float
        Multiply values in the file by this scale parameter.
    long_event_labels : bool
    max_gap : int

    .. note::
        The ``scale_factor`` attribute is not used in Phasespace C3D files;
        instead, use the POINT.SCALE parameter.

    .. note::
        The ``first_frame`` and ``last_frame`` header attributes are not used in
        C3D files generated by Phasespace. Instead, the first and last
        frame numbers are stored in the POINTS:ACTUAL_START_FIELD and
        POINTS:ACTUAL_END_FIELD parameters.
    '''

    # Read/Write header formats, read values as unsigned ints rather then floats.
    BINARY_FORMAT_WRITE = '<BBHHHHHfHHf274sHHH164s44s'
    BINARY_FORMAT_READ = '<BBHHHHHIHHI274sHHH164s44s'
    BINARY_FORMAT_READ_BIG_ENDIAN = '>BBHHHHHIHHI274sHHH164s44s'

    def __init__(self, handle=None):
        '''Create a new Header object.

        Parameters
        ----------
        handle : file handle, optional
            If given, initialize attributes for the Header from this file
            handle. The handle must be seek-able and readable. If `handle` is
            not given, Header attributes are initialized with default values.
        '''
        self.parameter_block = 2
        self.data_block = 3

        self.point_count = 50
        self.analog_count = 0

        self.first_frame = 1
        self.last_frame = 1
        self.analog_per_frame = 0
        self.frame_rate = 60.0

        self.max_gap = 0
        self.scale_factor = -1.0
        self.long_event_labels = False
        self.event_count = 0

        self.event_block = b''
        self.event_timings = np.zeros(0, dtype=np.float32)
        self.event_disp_flags = np.zeros(0, dtype=np.bool)
        self.event_labels = []

        if handle:
            self.read(handle)

    def write(self, handle):
        '''Write binary header data to a file handle.

        This method writes exactly 512 bytes to the beginning of the given file
        handle.

        Parameters
        ----------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be written to describe the parameters in this Header. The
            handle must be writeable.
        '''
        handle.seek(0)
        handle.write(struct.pack(self.BINARY_FORMAT_WRITE,
                                 # Pack vars:
                                 self.parameter_block,
                                 0x50,
                                 self.point_count,
                                 self.analog_count,
                                 self.first_frame,
                                 self.last_frame,
                                 self.max_gap,
                                 self.scale_factor,
                                 self.data_block,
                                 self.analog_per_frame,
                                 self.frame_rate,
                                 b'',
                                 self.long_event_labels and 0x3039 or 0x0,  # If True write long_event_key else 0
                                 self.event_count,
                                 0x0,
                                 self.event_block,
                                 b''))

    def __str__(self):
        '''Return a string representation of this Header's attributes.'''
        return '''\
                  parameter_block: {0.parameter_block}
                      point_count: {0.point_count}
                     analog_count: {0.analog_count}
                      first_frame: {0.first_frame}
                       last_frame: {0.last_frame}
                          max_gap: {0.max_gap}
                     scale_factor: {0.scale_factor}
                       data_block: {0.data_block}
                 analog_per_frame: {0.analog_per_frame}
                       frame_rate: {0.frame_rate}
                long_event_labels: {0.long_event_labels}
                      event_block: {0.event_block}'''.format(self)

    def read(self, handle, fmt=BINARY_FORMAT_READ):
        '''Read and parse binary header data from a file handle.

        This method reads exactly 512 bytes from the beginning of the given file
        handle.

        Parameters
        ----------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be read to initialize the attributes in this Header. The handle
            must be readable.

        fmt : Formating string used to read the header.

        Raises
        ------
        AssertionError
            If the magic byte from the header is not 80 (the C3D magic value).
        '''
        handle.seek(0)
        raw = handle.read(512)

        (self.parameter_block,
         magic,
         self.point_count,
         self.analog_count,
         self.first_frame,
         self.last_frame,
         self.max_gap,
         self.scale_factor,
         self.data_block,
         self.analog_per_frame,
         self.frame_rate,
         _,
         self.long_event_labels,
         self.event_count,
         __,
         self.event_block,
         _) = struct.unpack(fmt, raw)

        # Check magic number
        assert magic == 80, 'C3D magic {} != 80 !'.format(magic)

        # Check long event key
        self.long_event_labels = self.long_event_labels == 0x3039

    def _processor_convert(self, dtypes, handle):
        ''' Function interpreting the header once a processor type has been determined.
        '''

        if dtypes.is_dec:
            self.scale_factor = DEC_to_IEEE(self.scale_factor)
            self.frame_rate = DEC_to_IEEE(self.frame_rate)
            float_unpack = DEC_to_IEEE
        elif dtypes.is_ieee:
            self.scale_factor = UNPACK_FLOAT_IEEE(self.scale_factor)
            self.frame_rate = UNPACK_FLOAT_IEEE(self.frame_rate)
            float_unpack = UNPACK_FLOAT_IEEE
        elif dtypes.is_mips:
            # Re-read header in big-endian
            self.read(handle, Header.BINARY_FORMAT_READ_BIG_ENDIAN)
            # Then unpack
            self.scale_factor = UNPACK_FLOAT_IEEE(self.scale_factor)
            self.frame_rate = UNPACK_FLOAT_IEEE(self.frame_rate)
            float_unpack = UNPACK_FLOAT_IEEE

        self._parse_events(dtypes, float_unpack)

    def _parse_events(self, dtypes, float_unpack):
        ''' Parse the event section of the header.
        '''

        # Event section byte blocks
        time_bytes = self.event_block[:72]
        disp_bytes = self.event_block[72:90]
        label_bytes = self.event_block[92:]

        if dtypes.is_mips:
            unpack_fmt = '>I'
        else:
            unpack_fmt = '<I'

        read_count = self.event_count
        self.event_timings = np.zeros(read_count, dtype=np.float32)
        self.event_disp_flags = np.zeros(read_count, dtype=np.bool)
        self.event_labels = np.empty(read_count, dtype=object)
        for i in range(read_count):
            ilong = i * 4
            # Unpack
            self.event_disp_flags[i] = disp_bytes[i] > 0
            self.event_timings[i] = float_unpack(struct.unpack(unpack_fmt, time_bytes[ilong:ilong + 4])[0])
            self.event_labels[i] = dtypes.decode_string(label_bytes[ilong:ilong + 4])

    @property
    def events(self):
        ''' Get an iterable over displayed events defined in the header. Iterable items are on form (timing, label).

            Note*:
            Time as defined by the 'timing' is relative to frame 1 and not the 'first_frame' parameter.
            Frame 1 therefor has the time 0.0 in relation to the event timing.
        '''
        return zip(self.event_timings[self.event_disp_flags], self.event_labels[self.event_disp_flags])

    def encode_events(self, events):
        ''' Encode event data in the event block.

        Parameters
        ----------
        events : [(float, str), ...]
            Event data, iterable of touples containing the event timing and a 4 character label string.
             Event timings should be calculated relative to sample 1 with the timing 0.0s, and should
             not be relative to the first_frame header parameter.
        '''
        endian = '<'
        if sys.byteorder == 'big':
            endian = '>'

        # Event block format
        fmt = '{}{}{}{}{}'.format(endian,
                                  str(18 * 4) + 's',  # Timings
                                  str(18) + 's',      # Flags
                                  'H',                # __
                                  str(18 * 4) + 's'   # Labels
                                 )
        # Pack bytes
        event_timings = np.zeros(18, dtype=np.float32)
        event_disp_flags = np.zeros(18, dtype=np.uint8)
        event_labels = np.empty(18, dtype=object)
        label_bytes = bytearray(18 * 4)
        for i, (time, label) in enumerate(events):
            if i > 17:
                # Don't raise Error, header events are rarely used.
                warnings.warn('Maximum of 18 events can be encoded in the header, skipping remaining events.')
                break

            event_timings[i] = time
            event_labels[i] = label
            label_bytes[i * 4:(i + 1) * 4] = label.encode('utf-8')

        write_count = min(i + 1, 18)
        event_disp_flags[:write_count] = 1

        # Update event headers in self
        self.long_event_labels = 0x3039 # Magic number
        self.event_count = write_count
        # Update event block
        self.event_timings = event_timings[:write_count]
        self.event_disp_flags = np.ones(write_count, dtype=np.bool)
        self.event_labels = event_labels[:write_count]
        self.event_block = struct.pack(fmt,
                                       event_timings.tobytes(),
                                       event_disp_flags.tobytes(),
                                       0,
                                       label_bytes
                                      )
