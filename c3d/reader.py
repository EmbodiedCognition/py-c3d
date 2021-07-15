'''Contains the Reader class for reading C3D files.'''

import io
import numpy as np
import struct
import warnings
from .manager import Manager
from .header import Header
from .dtypes import DataTypes
from .utils import DEC_to_IEEE_BYTES


class Reader(Manager):
    '''This class provides methods for reading the data in a C3D file.

    A C3D file contains metadata and frame-based data describing 3D motion.

    You can iterate over the frames in the file by calling `read_frames()` after
    construction:

    >>> r = c3d.Reader(open('capture.c3d', 'rb'))
    >>> for frame_no, points, analog in r.read_frames():
    ...     print('{0.shape} points in this frame'.format(points))
    '''

    def __init__(self, handle):
        '''Initialize this C3D file by reading header and parameter data.

        Parameters
        ----------
        handle : file handle
            Read metadata and C3D motion frames from the given file handle. This
            handle is assumed to be `seek`-able and `read`-able. The handle must
            remain open for the life of the `Reader` instance. The `Reader` does
            not `close` the handle.

        Raises
        ------
        AssertionError
            If the metadata in the C3D file is inconsistent.
        '''
        super(Reader, self).__init__(Header(handle))

        self._handle = handle

        def seek_param_section_header():
            ''' Seek to and read the first 4 byte of the parameter header section '''
            self._handle.seek((self._header.parameter_block - 1) * 512)
            # metadata header
            return self._handle.read(4)

        # Begin by reading the processor type:
        buf = seek_param_section_header()
        _, _, parameter_blocks, processor = struct.unpack('BBBB', buf)
        self._dtypes = DataTypes(processor)
        # Convert header parameters in accordance with the processor type (MIPS format re-reads the header)
        self._header._processor_convert(self._dtypes, handle)

        # Restart reading the parameter header after parsing processor type
        buf = seek_param_section_header()

        start_byte = self._handle.tell()
        endbyte = start_byte + 512 * parameter_blocks - 4
        while self._handle.tell() < endbyte:
            chars_in_name, group_id = struct.unpack('bb', self._handle.read(2))
            if group_id == 0 or chars_in_name == 0:
                # we've reached the end of the parameter section.
                break
            name = self._dtypes.decode_string(self._handle.read(abs(chars_in_name))).upper()

            # Read the byte segment associated with the parameter and create a
            # separate binary stream object from the data.
            offset_to_next, = struct.unpack(['<h', '>h'][self._dtypes.is_mips], self._handle.read(2))
            if offset_to_next == 0:
                # Last parameter, as number of bytes are unknown,
                # read the remaining bytes in the parameter section.
                bytes = self._handle.read(endbyte - self._handle.tell())
            else:
                bytes = self._handle.read(offset_to_next - 2)
            buf = io.BytesIO(bytes)

            if group_id > 0:
                # We've just started reading a parameter. If its group doesn't
                # exist, create a blank one. add the parameter to the group.
                group = super(Reader, self).get(group_id)
                if group is None:
                    group = self._add_group(group_id)
                group.add_param(name, handle=buf)
            else:
                # We've just started reading a group. If a group with the
                # appropriate numerical id exists already (because we've
                # already created it for a parameter), just set the name of
                # the group. Otherwise, add a new group.
                group_id = abs(group_id)
                size, = struct.unpack('B', buf.read(1))
                desc = size and buf.read(size) or ''
                group = super(Reader, self).get(group_id)
                if group is not None:
                    self._rename_group(group, name)  # Inserts name key
                    group.desc = desc
                else:
                    self._add_group(group_id, name, desc)

        self._check_metadata()

    def read_frames(self, copy=True, analog_transform=True, check_nan=True, camera_sum=False):
        '''Iterate over the data frames from our C3D file handle.

        Parameters
        ----------
        copy : bool
            If False, the reader returns a reference to the same data buffers
            for every frame. The default is True, which causes the reader to
            return a unique data buffer for each frame. Set this to False if you
            consume frames as you iterate over them, or True if you store them
            for later.
        analog_transform : bool, default=True
            If True, ANALOG:SCALE, ANALOG:GEN_SCALE, and ANALOG:OFFSET transforms
            available in the file are applied to the analog channels.
        check_nan : bool, default=True
            If True, point x,y,z coordinates with nan values will be marked invalidated
            and residuals will be set to -1.
        camera_sum : bool, default=False
            Camera flag bits will be summed, converting the fifth column to a camera visibility counter.

        Returns
        -------
        frames : sequence of (frame number, points, analog)
            This method generates a sequence of (frame number, points, analog)
            tuples, one tuple per frame. The first element of each tuple is the
            frame number. The second is a numpy array of parsed, 5D point data
            and the third element of each tuple is a numpy array of analog
            values that were recorded during the frame. (Often the analog data
            are sampled at a higher frequency than the 3D point data, resulting
            in multiple analog frames per frame of point data.)

            The first three columns in the returned point data are the (x, y, z)
            coordinates of the observed motion capture point. The fourth column
            is an estimate of the error for this particular point, and the fifth
            column is the number of cameras that observed the point in question.
            Both the fourth and fifth values are -1 if the point is considered
            to be invalid.
        '''
        # Point magnitude scalar, if scale parameter is < 0 data is floating point
        # (in which case the magnitude is the absolute value)
        scale_mag = abs(self.point_scale)
        is_float = self.point_scale < 0

        if is_float:
            point_word_bytes = 4
        else:
            point_word_bytes = 2
        points = np.zeros((self.point_used, 5), np.float32)

        # TODO: handle ANALOG:BITS parameter here!
        p = self.get('ANALOG:FORMAT')
        analog_unsigned = p and p.string_value.strip().upper() == 'UNSIGNED'
        if is_float:
            analog_dtype = self._dtypes.float32
            analog_word_bytes = 4
        elif analog_unsigned:
            # Note*: Floating point is 'always' defined for both analog and point data, according to the standard.
            analog_dtype = self._dtypes.uint16
            analog_word_bytes = 2
            # Verify BITS parameter for analog
            p = self.get('ANALOG:BITS')
            if p and p._as_integer_value / 8 != analog_word_bytes:
                raise NotImplementedError('Analog data using {} bits is not supported.'.format(p._as_integer_value))
        else:
            analog_dtype = self._dtypes.int16
            analog_word_bytes = 2

        analog = np.array([], float)
        analog_scales, analog_offsets = self.get_analog_transform()

        # Seek to the start point of the data blocks
        self._handle.seek((self._header.data_block - 1) * 512)
        # Number of values (words) read in regard to POINT/ANALOG data
        N_point = 4 * self.point_used
        N_analog = self.analog_used * self.analog_per_frame

        # Total bytes per frame
        point_bytes = N_point * point_word_bytes
        analog_bytes = N_analog * analog_word_bytes
        # Parse the data blocks
        for frame_no in range(self.first_frame, self.last_frame + 1):
            # Read the byte data (used) for the block
            raw_bytes = self._handle.read(N_point * point_word_bytes)
            raw_analog = self._handle.read(N_analog * analog_word_bytes)
            # Verify read pointers (any of the two can be assumed to be 0)
            if len(raw_bytes) < point_bytes:
                warnings.warn('''reached end of file (EOF) while reading POINT data at frame index {}
                                 and file pointer {}!'''.format(frame_no - self.first_frame, self._handle.tell()))
                return
            if len(raw_analog) < analog_bytes:
                warnings.warn('''reached end of file (EOF) while reading POINT data at frame index {}
                                 and file pointer {}!'''.format(frame_no - self.first_frame, self._handle.tell()))
                return

            if is_float:
                # Convert every 4 byte words to a float-32 reprensentation
                # (the fourth column is still not a float32 representation)
                if self._dtypes.is_dec:
                    # Convert each of the first 6 16-bit words from DEC to IEEE float
                    points[:, :4] = DEC_to_IEEE_BYTES(raw_bytes).reshape((self.point_used, 4))
                else:  # If IEEE or MIPS:
                    # Convert each of the first 6 16-bit words to native float
                    points[:, :4] = np.frombuffer(raw_bytes,
                                                  dtype=self._dtypes.float32,
                                                  count=N_point).reshape((self.point_used, 4))

                # Cast last word to signed integer in system endian format
                last_word = points[:, 3].astype(np.int32)

            else:
                # View the bytes as signed 16-bit integers
                raw = np.frombuffer(raw_bytes,
                                    dtype=self._dtypes.int16,
                                    count=N_point).reshape((self.point_used, 4))
                # Read the first six 16-bit words as x, y, z coordinates
                points[:, :3] = raw[:, :3] * scale_mag
                # Cast last word to signed integer in system endian format
                last_word = raw[:, 3].astype(np.int16)

            # Parse camera-observed bits and residuals.
            # Notes:
            # - Invalid sample if residual is equal to -1 (check if word < 0).
            # - A residual of 0.0 represent modeled data (filtered or interpolated).
            # - Camera and residual words are always 8-bit (1 byte), never 16-bit.
            # - If floating point, the byte words are encoded in an integer cast to a float,
            #    and are written directly in byte form (see the MLS guide).
            ##
            # Read the residual and camera byte words (Note* if 32 bit word negative sign is discarded).
            residual_byte, camera_byte = (last_word & 0x00ff), (last_word & 0x7f00) >> 8

            # Fourth value is floating-point (scaled) error estimate (residual)
            points[:, 3] = residual_byte * scale_mag

            # Determine invalid samples
            invalid = last_word < 0
            if check_nan:
                is_nan = ~np.all(np.isfinite(points[:, :4]), axis=1)
                points[is_nan, :3] = 0.0
                invalid |= is_nan
            # Update discarded - sign
            points[invalid, 3] = -1

            # Fifth value is the camera-observation byte
            if camera_sum:
                # Convert to observation sum
                points[:, 4] = sum((camera_byte & (1 << k)) >> k for k in range(7))
            else:
                points[:, 4] = camera_byte  # .astype(np.float32)

            # Check if analog data exist, and parse if so
            if N_analog > 0:
                if is_float and self._dtypes.is_dec:
                    # Convert each of the 16-bit words from DEC to IEEE float
                    analog = DEC_to_IEEE_BYTES(raw_analog)
                else:
                    # Integer or INTEL/MIPS floating point data can be parsed directly
                    analog = np.frombuffer(raw_analog, dtype=analog_dtype, count=N_analog)

                # Reformat and convert
                analog = analog.reshape((-1, self.analog_used)).T
                analog = analog.astype(float)
                # Convert analog
                analog = (analog - analog_offsets) * analog_scales

            # Output buffers
            if copy:
                yield frame_no, points.copy(), analog  # .copy(), a new array is generated per frame for analog data.
            else:
                yield frame_no, points, analog

        # Function evaluating EOF, note that data section is written in blocks of 512
        final_byte_index = self._handle.tell()
        self._handle.seek(0, 2)  # os.SEEK_END)
        # Check if more then 1 block remain
        if self._handle.tell() - final_byte_index >= 512:
            warnings.warn('incomplete reading of data blocks. {} bytes remained after all datablocks were read!'.format(
                self._handle.tell() - final_byte_index))

    @property
    def proc_type(self) -> int:
        '''Get the processory type associated with the data format in the file.
        '''
        return self._dtypes.proc_type

    def to_writer(self, conversion=None):
        ''' Converts the reader to a `c3d.writer.Writer` instance using the conversion mode.

        See `c3d.writer.Writer.from_reader()` for supported conversion modes.
        '''
        from .writer import Writer
        return Writer.from_reader(self, conversion=conversion)

    def get(self, key, default=None):
        '''Get a readonly group or parameter.

        Parameters
        ----------
        key : str
            If this string contains a period (.), then the part before the
            period will be used to retrieve a group, and the part after the
            period will be used to retrieve a parameter from that group. If this
            string does not contain a period, then just a group will be
            returned.
        default : any
            Return this value if the named group and parameter are not found.

        Returns
        -------
        value : `c3d.group.GroupReadonly` or `c3d.parameter.ParamReadonly`
            Either a group or parameter with the specified name(s). If neither
            is found, returns the default value.
        '''
        val = super(Reader, self).get(key)
        if val:
            return val.readonly()
        return default

    def items(self):
        ''' Get iterable over pairs of (str, `c3d.group.GroupReadonly`) entries.
        '''
        return ((k, v.readonly()) for k, v in super(Reader, self).items())

    def values(self):
        ''' Get iterable over `c3d.group.GroupReadonly` entries.
        '''
        return (v.readonly() for k, v in super(Reader, self).items())

    def listed(self):
        ''' Get iterable over pairs of (int, `c3d.group.GroupReadonly`) entries.
        '''
        return ((k, v.readonly()) for k, v in super(Reader, self).listed())
