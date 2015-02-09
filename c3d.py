'''A Python library for reading and writing C3D files.'''

import array
import io
import numpy as np
import struct
import warnings


PROCESSOR_INTEL = 84
PROCESSOR_DEC = 85
PROCESSOR_MIPS = 86


class Header(object):
    '''Header information from a C3D file.

    Attributes
    ----------
    label_block : int
        Index of the 512-byte block where labels (metadata) are found.
    parameter_block : int
        Index of the 512-byte block where parameters (metadata) are found.
    data_block : int
        Index of the 512-byte block where data starts.
    point_count : int
        Number of motion capture points recorded in this file.
    analog_count : int
        Number of analog channels recorded in this file.
    first_frame : int
        Index of the first frame of data.

        This is actually not used in Phasespace data files; instead, the first
        frame number is stored in the POINTS:ACTUAL_START_FIELD parameter.
    last_frame : int
        Index of the last frame of data.

        This is actually not used in Phasespace data files; instead, the last
        frame number is stored in the POINTS:ACTUAL_END_FIELD parameter.
    sample_per_frame : int
        Number of samples per frame. Seems to be unused in Phasespace files.
    frame_rate : float
        The frame rate of the recording, in frames per second.
    scale_factor : float
        Multiply values in the file by this scale parameter.

        This is actually not used in Phasespace C3D files; instead, use the
        POINT.SCALE parameter.
    long_event_labels : bool
    max_gap : int
    '''

    BINARY_FORMAT = '<BBHHHHHfHHf270sHH214s'

    def __init__(self, handle=None):
        '''Create a new Header object.

        Parameters
        ----------
        handle : file handle, optional
            If given, initialize attributes for the Header from this file
            handle. The handle must be seek-able and readable. If `handle` is
            not given, Header attributes are initialized with default values.
        '''
        self.label_block = 0
        self.parameter_block = 2
        self.data_block = 3

        self.point_count = 50
        self.analog_count = 0

        self.first_frame = 1
        self.last_frame = 1
        self.sample_per_frame = 0
        self.frame_rate = 60.0

        self.max_gap = 0
        self.scale_factor = -1.0
        self.long_event_labels = False

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
        handle.write(struct.pack(self.BINARY_FORMAT,
                                 self.parameter_block,
                                 0x50,
                                 self.point_count,
                                 self.analog_count,
                                 self.first_frame,
                                 self.last_frame,
                                 self.max_gap,
                                 self.scale_factor,
                                 self.data_block,
                                 self.sample_per_frame,
                                 self.frame_rate,
                                 '',
                                 self.long_event_labels and 0x3039 or 0x0,
                                 self.label_block,
                                 ''))

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
 sample_per_frame: {0.sample_per_frame}
       frame_rate: {0.frame_rate}
long_event_labels: {0.long_event_labels}
      label_block: {0.label_block}'''.format(self)

    def read(self, handle):
        '''Read and parse binary header data from a file handle.

        This method reads exactly 512 bytes from the beginning of the given file
        handle.

        Parameters
        ----------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be read to initialize the attributes in this Header. The handle
            must be readable.

        Raises
        ------
        AssertionError
            If the magic byte from the header is not 80 (the C3D magic value).
        '''
        handle.seek(0)
        (self.parameter_block,
         magic,
         self.point_count,
         self.analog_count,
         self.first_frame,
         self.last_frame,
         self.max_gap,
         self.scale_factor,
         self.data_block,
         self.sample_per_frame,
         self.frame_rate,
         _,
         self.long_event_labels,
         self.label_block,
         _) = struct.unpack(self.BINARY_FORMAT, handle.read(512))

        assert magic == 80, 'C3D magic {} != 80 !'.format(magic)


class Param(object):
    '''A class representing a single named parameter from a C3D file.

    Attributes
    ----------
    name : str
        Name of this parameter.
    desc : str
        Brief description of this parameter.
    bytes_per_element : int, optional
        For array data, this describes the size of each element of data. For
        string data (including arrays of strings), this should be -1.
    dimensions : list of int
        For array data, this describes the dimensions of the array, stored in
        column-major order. For arrays of strings, the dimensions here will be
        the number of columns (length of each string) followed by the number of
        rows (number of strings).
    bytes : str
        Raw data for this parameter.
    '''

    def __init__(self,
                 name,
                 desc='',
                 bytes_per_element=1,
                 dimensions=None,
                 bytes='',
                 handle=None):
        '''Set up a new parameter, only the name is required.'''
        self.name = name
        self.desc = desc
        self.bytes_per_element = bytes_per_element
        self.dimensions = dimensions or []
        self.bytes = bytes
        if handle:
            self.read(handle)

    def __repr__(self):
        return '<Param: {}>'.format(self.desc)

    @property
    def num_elements(self):
        '''Return the number of elements in this parameter's array value.'''
        e = 1
        for d in self.dimensions:
            e *= d
        return e

    @property
    def total_bytes(self):
        '''Return the number of bytes used for storing this parameter's data.'''
        return self.num_elements * abs(self.bytes_per_element)

    def binary_size(self):
        '''Return the number of bytes needed to store this parameter.'''
        return (
            1 + # group_id
            2 + # next offset marker
            1 + len(self.name.encode('utf-8')) + # size of name and name bytes
            1 + # data size
            1 + len(self.dimensions) + # size of dimensions and dimension bytes
            self.total_bytes + # data
            1 + len(self.desc.encode('utf-8')) # size of desc and desc bytes
            )

    def write(self, group_id, handle):
        '''Write binary data for this parameter to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group that holds this parameter.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self.name.encode('utf-8')
        handle.write(struct.pack('bb', len(name), group_id))
        handle.write(name)
        handle.write(struct.pack('<h', self.binary_size() - 2 - len(name)))
        handle.write(struct.pack('b', self.bytes_per_element))
        handle.write(struct.pack('B', len(self.dimensions)))
        handle.write(struct.pack('B' * len(self.dimensions), *self.dimensions))
        if self.bytes:
            handle.write(self.bytes)
        desc = self.desc.encode('utf-8')
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)

    def read(self, handle):
        '''Read binary data for this parameter from a file handle.

        This reads exactly enough data from the current position in the file to
        initialize the parameter.
        '''
        self.bytes_per_element, = struct.unpack('b', handle.read(1))
        dims, = struct.unpack('B', handle.read(1))
        self.dimensions = [struct.unpack('B', handle.read(1))[0] for _ in range(dims)]
        self.bytes = ''
        if self.total_bytes:
            self.bytes = handle.read(self.total_bytes)
        size, = struct.unpack('B', handle.read(1))
        self.desc = size and handle.read(size).decode('utf-8') or ''

    def _as(self, fmt):
        '''Unpack the raw bytes of this param using the given struct format.'''
        return struct.unpack('<' + fmt, self.bytes)[0]

    @property
    def int8_value(self):
        '''Get the param as an 8-bit signed integer.'''
        return self._as('b')

    @property
    def uint8_value(self):
        '''Get the param as an 8-bit unsigned integer.'''
        return self._as('B')

    @property
    def int16_value(self):
        '''Get the param as a 16-bit signed integer.'''
        return self._as('h')

    @property
    def uint16_value(self):
        '''Get the param as a 16-bit unsigned integer.'''
        return self._as('H')

    @property
    def int32_value(self):
        '''Get the param as a 32-bit signed integer.'''
        return self._as('i')

    @property
    def uint32_value(self):
        '''Get the param as a 32-bit unsigned integer.'''
        return self._as('I')

    @property
    def float_value(self):
        '''Get the param as a 32-bit float.'''
        return self._as('f')

    @property
    def bytes_value(self):
        '''Get the param as a raw byte string.'''
        return self.bytes

    @property
    def string_value(self):
        '''Get the param as a unicode string.'''
        return self.bytes.decode('utf-8')

    def _as_array(self, fmt):
        '''Unpack the raw bytes of this param using the given data format.'''
        assert self.dimensions, \
            '{}: cannot get value as {} array!'.format(self.name, fmt)
        elems = array.array(fmt)
        elems.fromstring(self.bytes)
        return np.array(elems).reshape(self.dimensions)

    @property
    def int8_array(self):
        '''Get the param as an array of 8-bit signed integers.'''
        return self._as_array('b')

    @property
    def uint8_array(self):
        '''Get the param as an array of 8-bit unsigned integers.'''
        return self._as_array('B')

    @property
    def int16_array(self):
        '''Get the param as a array of 16-bit signed integers.'''
        return self._as_array('h')

    @property
    def uint16_array(self):
        '''Get the param as a array of 16-bit unsigned integers.'''
        return self._as_array('H')

    @property
    def int32_array(self):
        '''Get the param as a array of 32-bit signed integers.'''
        return self._as_array('i')

    @property
    def uint32_array(self):
        '''Get the param as a array of 32-bit unsigned integers.'''
        return self._as_array('I')

    @property
    def float_array(self):
        '''Get the param as a array of 32-bit floats.'''
        return self._as_array('f')

    @property
    def bytes_array(self):
        '''Get the param as a array of raw byte strings.'''
        assert len(self.dimensions) == 2, \
            '{}: cannot get value as bytes array!'.format(self.name)
        l, n = self.dimensions
        return [self.bytes[i*l:(i+1)*l] for i in range(n)]

    @property
    def string_array(self):
        '''Get the param as a array of unicode strings.'''
        assert len(self.dimensions) == 2, \
            '{}: cannot get value as string array!'.format(self.name)
        l, n = self.dimensions
        return [self.bytes[i*l:(i+1)*l].decode('utf-8') for i in range(n)]


class Group(dict):
    '''A group of parameters from a C3D file.

    In C3D files, parameters are organized in groups. Each group has a name, a
    description, and a set of named parameters.

    Attributes
    ----------
    name : str
        Name of this parameter group.
    desc : str
        Description for this parameter group.
    '''

    def __init__(self, name=None, desc=None):
        self.name = name
        self.desc = desc

    def __repr__(self):
        return '<Group: {}>'.format(self.desc)

    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        Additional keyword arguments will be passed to the `Param` constructor.
        '''
        self[name.upper()] = Param(name.upper(), **kwargs)

    def binary_size(self):
        '''Return the number of bytes to store this group and its parameters.'''
        return (
            1 + # group_id
            1 + len(self.name.encode('utf-8')) + # size of name and name bytes
            2 + # next offset marker
            1 + len(self.desc.encode('utf-8')) + # size of desc and desc bytes
            sum(p.binary_size() for p in self.values()))

    def write(self, group_id, handle):
        '''Write this parameter group, with parameters, to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group.
        handle : file handle
            An open, writable, binary file handle.
        '''
        handle.write(struct.pack('bb', len(self.name), -group_id))
        handle.write(self.name)
        handle.write(struct.pack('<h', 3 + len(self.desc)))
        handle.write(struct.pack('B', len(self.desc)))
        handle.write(self.desc)
        for param in self.values():
            param.write(group_id, handle)

    def get_int8(self, key):
        '''Get the value of the given parameter as an 8-bit signed integer.'''
        return self[key.upper()].int8_value

    def get_uint8(self, key):
        '''Get the value of the given parameter as an 8-bit unsigned integer.'''
        return self[key.upper()].uint8_value

    def get_int16(self, key):
        '''Get the value of the given parameter as a 16-bit signed integer.'''
        return self[key.upper()].int16_value

    def get_uint16(self, key):
        '''Get the value of the given parameter as a 16-bit unsigned integer.'''
        return self[key.upper()].uint16_value

    def get_int32(self, key):
        '''Get the value of the given parameter as a 32-bit signed integer.'''
        return self[key.upper()].int32_value

    def get_uint32(self, key):
        '''Get the value of the given parameter as a 32-bit unsigned integer.'''
        return self[key.upper()].uint32_value

    def get_float(self, key):
        '''Get the value of the given parameter as a 32-bit float.'''
        return self[key.upper()].float_value

    def get_bytes(self, key):
        '''Get the value of the given parameter as a byte array.'''
        return self[key.upper()].bytes_value

    def get_string(self, key):
        '''Get the value of the given parameter as a string.'''
        return self[key.upper()].string_value


class Manager(dict):
    '''A base class for managing C3D file metadata.

    This class manages a C3D header (which contains some stock metadata fields)
    as well as a set of parameter groups. Each group is accessible using its
    name.

    Attributes
    ----------
    header : `Header`
        Header information for the C3D file.
    '''

    def __init__(self, header=None):
        '''Set up a new Manager with a Header.'''
        self.header = header or Header()

    def check_metadata(self):
        '''Ensure that the metadata in our file is self-consistent.'''
        assert self.header.point_count == self.points_per_frame(), (
            'inconsistent point count! {} header != {} parameter'.format(
                self.header.point_count,
                self.points_per_frame(),
            ))

        assert self.header.scale_factor == self.scale_factor(), (
            'inconsistent scale factor! {} header != {} parameter'.format(
                self.header.scale_factor,
                self.scale_factor(),
            ))

        assert self.header.frame_rate == self.frame_rate(), (
            'inconsistent frame rate! {} header != {} parameter'.format(
                self.header.frame_rate,
                self.frame_rate(),
            ))

        apf = self.analog_per_frame() * self.analog_frame_rate() / self.frame_rate()
        assert self.header.analog_count == apf, (
            'inconsistent analog count! {} header != {} analog per frame * '
            '{} analog-fps / {} point-fps'.format(
                self.header.analog_count,
                self.analog_per_frame(),
                self.analog_frame_rate(),
                self.frame_rate(),
            ))

        start = self.get_uint16('POINT:DATA_START')
        assert self.header.data_block == start, (
            'inconsistent data block! {} header != {} parameter'.format(
                self.header.data_block, start))

        for name in ('POINT:LABELS', 'POINT:DESCRIPTIONS',
                     'ANALOG:USED', 'ANALOG:LABELS', 'ANALOG:DESCRIPTIONS'):
            if self.get(name) is None:
                warnings.warn('missing parameter {}'.format(name))

    def add_group(self, group_id, name, desc):
        '''Add a new parameter group.

        Parameters
        ----------
        group_id : int
            The numeric ID for a group to check or create.
        name : str, optional
            If a group is created, assign this name to the group.
        desc : str, optional
            If a group is created, assign this description to the group.

        Returns
        -------
        Group :
            A :class:`Group` with the given ID, name, and description.

        Raises
        ------
        KeyError
            If a group with a duplicate ID or name already exists.
        '''
        if group_id in self:
            raise KeyError(group_id)
        name = name.upper()
        if name in self:
            raise KeyError(name)
        group = self[name] = self[group_id] = Group(name, desc)
        return group

    def get(self, group, default=None):
        '''Get a group or parameter.

        Parameters
        ----------
        group : str
            If this string contains a period (.), then the part before the
            period will be used to retrieve a group, and the part after the
            period will be used to retrieve a parameter from that group. If this
            string does not contain a period, then just a group will be
            returned.
        default : any
            Return this value if the named group and parameter are not found.

        Returns
        -------
        Group or Param :
            Either a :class:`Group` or a :class:`Param` with the specified
            name(s). If neither is found, returns the default value.
        '''
        try:
            return self[group]
        except KeyError:
            return default

    def __getitem__(self, group):
        '''Get a group or parameter.

        Parameters
        ----------
        group : str
            If this string contains a colon (:) or a period (.), then the part
            before the punctuation will be used to retrieve a group, and the
            part after the punctuation will be used to retrieve a parameter from
            that group. If this string does not contain a period, then just a
            group will be returned.

        Returns
        -------
        Group or Param :
            Either a :class:`Group` or a :class:`Param` with the specified
            name(s).

        Raises
        ------
        KeyError
            If no group and parameter with the given identifiers are found.
        '''
        if isinstance(group, int):
            return super(Manager, self).__getitem__(group)
        group = group.upper()
        param = None
        if '.' in group:
            group, param = group.split('.', 1)
        if ':' in group:
            group, param = group.split(':', 1)
        group = super(Manager, self).__getitem__(group)
        if param is not None:
            return group[param]
        return group

    def get_int8(self, key):
        '''Get a parameter value as an 8-bit signed integer.'''
        return self[key].int8_value

    def get_uint8(self, key):
        '''Get a parameter value as an 8-bit unsigned integer.'''
        return self[key].uint8_value

    def get_int16(self, key):
        '''Get a parameter value as a 16-bit signed integer.'''
        return self[key].int16_value

    def get_uint16(self, key):
        '''Get a parameter value as a 16-bit unsigned integer.'''
        return self[key].uint16_value

    def get_int32(self, key):
        '''Get a parameter value as a 32-bit signed integer.'''
        return self[key].int32_value

    def get_uint32(self, key):
        '''Get a parameter value as a 32-bit unsigned integer.'''
        return self[key].uint32_value

    def get_float(self, key):
        '''Get a parameter value as a 32-bit float.'''
        return self[key].float_value

    def get_bytes(self, key):
        '''Get a parameter value as a byte string.'''
        return self[key].bytes_value

    def get_string(self, key):
        '''Get a parameter value as a string.'''
        return self[key].string_value

    def parameter_blocks(self):
        '''Compute the size (in 512B blocks) of the parameter section.'''
        bytes = 4. + sum(g.binary_size() for g in self.values())
        return int(np.ceil(bytes / 512))

    def frame_rate(self):
        return self.get_float('POINT:RATE')

    def scale_factor(self):
        return self.get_float('POINT:SCALE')

    def points_per_frame(self):
        return self.get_uint16('POINT:USED')

    num_points = points_per_frame

    def analog_per_frame(self):
        return self.get_uint16('ANALOG:USED')

    num_analog = analog_per_frame

    def analog_frame_rate(self):
        return self.get_float('ANALOG:RATE')

    def point_labels(self):
        return self.get('POINT:LABELS').string_array

    def first_frame(self):
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self.get('TRIAL:ACTUAL_START_FIELD')
        if param is not None:
            return param.int32_value
        return self.header.first_frame

    def last_frame(self):
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self.get('TRIAL:ACTUAL_END_FIELD')
        if param is not None:
            return param.int32_value
        return self.header.last_frame


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
        ValueError
            If the processor metadata in the C3D file is anything other than 84
            (Intel format).
        '''
        super(Reader, self).__init__(Header(handle))

        self._handle = handle
        self._handle.seek((self.header.parameter_block - 1) * 512)

        # metadata header
        buf = self._handle.read(4)
        _, _, parameter_blocks, processor = struct.unpack('BBBB', buf)
        if processor != PROCESSOR_INTEL:
            raise ValueError(
                'we only read Intel C3D files (got processor {})'.
                format(processor))

        # read all parameter blocks as a single chunk to avoid block
        # boundary issues.
        bytes = self._handle.read(512 * parameter_blocks - 4)
        while bytes:
            buf = io.BytesIO(bytes)

            chars_in_name, group_id = struct.unpack('bb', buf.read(2))
            if group_id == 0 or chars_in_name == 0:
                # we've reached the end of the parameter section.
                break

            name = buf.read(abs(chars_in_name)).decode('utf-8').upper()
            offset_to_next, = struct.unpack('<h', buf.read(2))

            if group_id > 0:
                # we've just started reading a parameter. if its group doesn't
                # exist, create a blank one. add the parameter to the group.
                self.setdefault(group_id, Group()).add_param(name, handle=buf)
            else:
                # we've just started reading a group. if a group with the
                # appropriate id exists already (because we've already created
                # it for a parameter), just set the name of the group.
                # otherwise, add a new group.
                group_id = abs(group_id)
                size, = struct.unpack('B', buf.read(1))
                desc = size and buf.read(size) or ''
                group = self.get(group_id)
                if group is not None:
                    group.name = name
                    group.desc = desc
                    self[name] = group
                else:
                    self.add_group(group_id, name, desc)

            bytes = bytes[2 + abs(chars_in_name) + offset_to_next:]

        self.check_metadata()

    def read_frames(self, copy=True):
        '''Iterate over the data frames from our C3D file handle.

        Parameters
        ----------
        copy : bool
            If False, the reader returns a reference to the same data buffers
            for every frame. The default is True, which causes the reader to
            return a unique data buffer for each frame. Set this to False if you
            consume frames as you iterate over them, or True if you store them
            for later.

        Returns
        -------
        sequence of (frame number, points, analog) :
            This method generates a sequence of (frame number, points, analog)
            tuples, one tuple per frame. The first element of each tuple is the
            frame number. The second is a numpy array of parsed, 5D point data
            and the third element of each tuple is a numpy array of analog
            values that were recorded during the frame. (Often the analog data
            are sampled at a higher frequency than the 3D point data, resulting
            in multiple analog frames per frame of point data.)

            The first three columns in the returned point data are the (x, y, z)
            coordinates of the observed motion capture point. The fourth value
            is an estimate of the error for this particular point, and the fifth
            value is the number of cameras that observed the point in question.
            Both the fourth and fifth values are -1 if the point is considered
            to be invalid.
        '''
        ppf = self.points_per_frame()
        apf = self.analog_per_frame()

        scale = abs(self.scale_factor())
        is_float = self.scale_factor() < 0

        point_dtype = [np.int16, np.float32][is_float]
        point_scale = [scale, 1][is_float]
        points = np.zeros((ppf, 5), float)

        # TODO: handle ANALOG:BITS parameter here!
        p = self.get('ANALOG:FORMAT')
        analog_unsigned = p and p.string_value.strip().upper() == 'UNSIGNED'
        analog_dtype = np.int16
        if is_float:
            analog_dtype = np.float32
        elif analog_unsigned:
            analog_dtype = np.uint16
        analog = np.array([], float)

        offsets = np.zeros((apf, ), int)
        param = self.get('ANALOG:OFFSET')
        if param is not None:
            offsets = param.int16_array[:apf]

        scales = np.ones((apf, ), float)
        param = self.get('ANALOG:SCALE')
        if param is not None:
            scales = param.float_array[:apf]

        gen_scale = 1.
        param = self.get('ANALOG:GEN_SCALE')
        if param is not None:
            gen_scale = param.float_value

        self._handle.seek((self.header.data_block - 1) * 512)
        for frame_no in range(self.first_frame(), self.last_frame() + 1):
            raw = np.fromfile(self._handle, dtype=point_dtype,
                count=4 * self.header.point_count).reshape((ppf, 4))

            points[:, :3] = raw[:, :3] * point_scale

            valid = raw[:, 3] > -1
            points[~valid, 3:5] = -1
            c = raw[valid, 3].astype(np.uint16)

            # fourth value is floating-point (scaled) error estimate
            points[valid, 3] = (c & 0xff).astype(float) * scale

            # fifth value is number of bits set in camera-observation byte
            points[valid, 4] = sum((c & (1 << k)) >> k for k in range(8, 17))

            if self.header.analog_count > 0:
                raw = np.fromfile(self._handle, dtype=analog_dtype,
                    count=self.header.analog_count).reshape((-1, apf))
                analog = (raw.astype(float) - offsets) * scales * gen_scale

            if copy:
                yield frame_no, points.copy(), analog.copy()
            else:
                yield frame_no, points, analog


class Writer(Manager):
    '''This class manages the task of writing metadata and frames to a C3D file.

    >>> r = c3d.Reader(open('data.c3d', 'rb'))
    >>> frames = smooth_frames(r.read_frames())
    >>> w = c3d.Writer(open('smoothed.c3d', 'wb'))
    >>> w.write_from_reader(frames, r)
    '''

    def __init__(self, handle):
        '''Initialize a new Writer with a file handle.

        Parameters
        ----------
        handle : file handle
            Write metadata and C3D motion frames to the given file handle. This
            handle is assumed to be `seek`-able and `write`-able. The handle
            must remain open for the life of the `Writer` instance. The `Writer`
            does not `close` the handle.
        '''
        super(Writer, self).__init__()
        self._handle = handle

    def _pad_block(self):
        '''Pad the file with 0s to the end of the next block boundary.'''
        extra = self._handle.tell() % 512
        if extra:
            self._handle.write('\x00' * (512 - extra))

    def write_metadata(self):
        '''Write metadata for this file to our file handle.'''
        self.check_metadata()

        # header
        self.header.write(self._handle)
        self._pad_block()
        assert self._handle.tell() == 512

        # groups
        self._handle.write(
            struct.pack('BBBB', 0, 0, self.parameter_blocks(), PROCESSOR_INTEL))
        id_groups = sorted((i, g) for i, g in self.items() if isinstance(i, int))
        for group_id, group in id_groups:
            group.write(group_id, self._handle)

        # padding
        self._pad_block()
        while self._handle.tell() != 512 * (self.header.data_block - 1):
            self._handle.write('\x00' * 512)

    def write_frames(self, frames):
        '''Write the given list of frame data to our file handle.

        frames : sequence of frame data
            A sequence of (points, analog) tuples, each containing data for one
            frame.
        '''
        assert self._handle.tell() == 512 * (self.header.data_block - 1)
        format = 'fi'[self.scale_factor() >= 0]
        for p, a in frames:
            point = array.array(format)
            point.extend(p.flatten())
            point.tofile(self._handle)
            analog = array.array(format)
            analog.extend(a)
            analog.tofile(self._handle)
        self._pad_block()

    def write_like_phasespace(self, frames, frame_count,
                              point_frame_rate=480.0,
                              analog_frame_rate=0.0,
                              point_scale_factor=-1.0,
                              point_units='mm  ',
                              gen_scale=1.0,
                              ):
        '''Write a set of frames to a file so it looks like Phasespace wrote it.

        Parameters
        ----------
        frames : sequence of frame data
            The sequence of frames to write.
        frame_count : int
            The number of frames to write.
        point_frame_rate : float
            The frame rate of the data.
        analog_frame_rate : float
            The number of analog samples per frame.
        point_scale_factor : float
            The scale factor for point data.
        point_units : str
            The units that the point numbers represent.
        '''
        try:
            points, analog = iter(frames).next()
        except StopIteration:
            return

        # POINT group
        ppf = len(points)
        point_group = self.add_group(1, 'POINT', 'POINT group')
        point_group.add_param(
            'USED', desc='Number of 3d markers', data_size=2,
            bytes=struct.pack('<H', ppf))
        point_group.add_param(
            'FRAMES', desc='frame count', data_size=2,
            bytes=struct.pack('<H', min(65535, frame_count)))
        point_group.add_param(
            'DATA_START', desc='data block number', data_size=2,
            bytes=struct.pack('<H', 0))
        point_group.add_param(
            'SCALE', desc='3d scale factor', data_size=4,
            bytes=struct.pack('<f', point_scale_factor))
        point_group.add_param(
            'RATE', desc='3d data capture rate', data_size=4,
            bytes=struct.pack('<f', point_frame_rate))
        point_group.add_param(
            'X_SCREEN', desc='X_SCREEN parameter',
            data_size=-1, dimensions=[2], bytes='+X')
        point_group.add_param(
            'Y_SCREEN', desc='Y_SCREEN parameter',
            data_size=-1, dimensions=[2], bytes='+Z')
        point_group.add_param(
            'UNITS', desc='3d data units', data_size=-1,
            dimensions=[len(point_units)], bytes=point_units)
        point_group.add_param(
            'LABELS', desc='labels', data_size=-1, dimensions=[5, ppf],
            bytes=''.join('M%03d ' % i for i in range(ppf)))
        point_group.add_param(
            'DESCRIPTIONS', desc='descriptions', data_size=-1,
            dimensions=[16, ppf], bytes=' ' * 16 * ppf)

        # ANALOG group
        apf = len(analog)
        analog_group = self.add_group(2, 'ANALOG', 'ANALOG group')
        analog_group.add_param(
            'USED', desc='analog channel count', data_size=2,
            bytes=struct.pack('<H', apf))
        analog_group.add_param(
            'RATE', desc='analog frame rate', data_size=4,
            bytes=struct.pack('<f', analog_frame_rate))
        analog_group.add_param(
            'GEN_SCALE', desc='analog general scale factor', data_size=4,
            bytes=struct.pack('<f', gen_scale))
        analog_group.add_param(
            'SCALE', desc='analog channel scale factors', data_size=4,
            dimensions=[0])
        analog_group.add_param(
            'OFFSET', desc='analog channel offsets', data_size=2,
            dimensions=[0])

        # TRIAL group
        trial_group = self.add_group(3, 'TRIAL', 'TRIAL group')
        trial_group.add_param(
            'ACTUAL_START_FIELD', desc='actual start frame', data_size=2,
            dimensions=[2], bytes=struct.pack('<I', 1))
        trial_group.add_param(
            'ACTUAL_END_FIELD', desc='actual end frame', data_size=2,
            dimensions=[2], bytes=struct.pack('<I', frame_count))

        # sync parameter information to header.
        blocks = self.parameter_blocks()
        point_group['DATA_START'].bytes = struct.pack('<H', 2 + blocks)

        self.header.data_block = 2 + blocks
        self.header.frame_rate = point_frame_rate
        self.header.last_frame = min(frame_count, 65535)
        self.header.point_count = ppf
        self.header.analog_count = apf
        self.header.scale_factor = point_scale_factor

        self.write_metadata()
        self.write_frames(frames)

    def write_from_reader(self, frames, reader):
        '''Write a file with the same metadata and number of frames as a Reader.

        frames: A sequence of frames to write.
        reader: Copy metadata from this reader to the output file.
        '''
        self.write_like_phasespace(frames, reader.end_field(), reader.frame_rate())
