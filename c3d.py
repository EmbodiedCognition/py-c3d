# Copyright (c) 2010 Leif Johnson <leif@leifjohnson.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''A Python library for reading and writing C3D files.'''

import array
import numpy
import struct
import operator
import cStringIO
import warnings


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

        This is actually not used in Phasespace data files; instead, to seek to
        data, use the POINTS.ACTUAL_START_FIELD parameter.
    last_frame : int
        Index of the last frame of data.

        This is actually not used in Phasespace data files; instead, to seek to
        data, use the POINTS.ACTUAL_END_FIELD parameter.
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

        Arguments
        ---------
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

        Arguments
        ---------
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

        Arguments
        ---------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be read to initialize the attributes in this Header. The handle
            must be readable.

        Raises
        ------
        AssertionError, if the magic byte from the header is not 80 (the C3D
        magic value).
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
                 bytes=None,
                 handle=None):
        '''Set up a new parameter with at least a name.

        name : str
            The name of the parameter.
        desc : str, optional
            The description of the parameter.
        bytes_per_element : int, optional
            For array data, this describes the size of each element of data. For
            string data (including arrays of strings), this should be -1.
        dimensions : list of int, optional
            For array data, this describes the dimensions of the array, stored
            in row-major order.
        bytes : str, optional
            The raw bytes for this parameter. Use struct.pack() to construct
            this value, or just pass the raw string data for string parameters.
        handle : file handle, optional
            If provided, the data for the parameter will be read from this
            file handle. The handle must be readable.
        '''
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
        return reduce(operator.mul, self.dimensions, 1)

    @property
    def total_bytes(self):
        '''Return the number of bytes used for storing this parameter's data.'''
        return self.num_elements * abs(self.bytes_per_element)

    def binary_size(self):
        '''Return the number of bytes needed to store this parameter.'''
        return (
            1 + # group_id
            2 + # next offset marker
            1 + len(self.name) + # size of name and name bytes
            1 + # data size
            1 + len(self.dimensions) + # size of dimensions and dimension bytes
            self.total_bytes + # data
            1 + len(self.desc) # size of desc and desc bytes
            )

    def write(self, handle):
        '''Write binary data for this parameter to a file handle.

        This writes data at the current position in the file.
        '''
        handle.write(struct.pack('b', self.bytes_per_element))
        handle.write(struct.pack('B', len(self.dimensions)))
        handle.write(struct.pack('B' * len(self.dimensions), *self.dimensions))
        if self.bytes:
            handle.write(self.bytes)
        handle.write(struct.pack('B', len(self.desc)))
        handle.write(self.desc)

    def read(self, handle):
        '''Read binary data for this parameter from a file handle.

        This reads exactly enough data from the current position in the file to
        initialize the parameter.
        '''
        self.bytes_per_element, = struct.unpack('b', handle.read(1))
        dims, = struct.unpack('B', handle.read(1))
        self.dimensions = [struct.unpack('B', handle.read(1))[0] for _ in range(dims)]
        self.bytes = None
        if self.total_bytes:
            self.bytes = handle.read(self.total_bytes)
        size, = struct.unpack('B', handle.read(1))
        self.desc = size and handle.read(size) or ''

    def __str__(self):
        '''Return a friendly string representation of this parameter.'''
        kwargs = self.__dict__.copy()
        kwargs['shaped'] = ''
        if self.bytes:
            kwargs['bytes'] = '{}{}'.format(
                self.bytes[:10], ['', '...'][len(self.bytes) > 10])
            if len(self.dimensions) == 2:
                C, R = self.dimensions
                kwargs['shaped'] = ' ->\n' + '\n'.join(
                    repr(self.bytes[r * C:(r+1) * C]) for r in range(R))
            if len(self.dimensions) == 0:
                fmt = '<' + {2: 'H', 4: 'f'}.get(len(self.bytes), 'B')
                kwargs['shaped'] = ' -> ' + struct.unpack(fmt, self.bytes)[0]

        return '''\
      name: {0.name}
      desc: {0.desc}
 data_size: {0.data_size}
dimensions: {0.dimensions}
     bytes: {0.bytes:r}{0.shaped}'''.format(kwargs)

    def _as(self, fmt):
        '''Unpack the raw bytes of this param using the given struct format.'''
        return struct.unpack(fmt, self.bytes)[0]

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
    def string_value(self):
        '''Get the param as a raw byte string.'''
        return self.bytes


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

        Arguments
        ---------
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
            1 + len(self.name) + # size of name and name bytes
            2 + # next offset marker
            1 + len(self.desc) + # size of desc and desc bytes
            sum(p.binary_size() for p in self.params.itervalues()))

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

    def add_group(self, group_id, name, desc):
        '''Add a new parameter group.

        Arguments
        ---------
        group_id : int
            The numeric ID for a group to check or create.
        name : str, optional
            If a group is created, assign this name to the group.
        desc : str, optional
            If a group is created, assign this description to the group.

        Returns
        -------
        A `Group` with the given ID, name, and description.

        Raises
        ------
        KeyError, if a group with a duplicate ID or name already exists.
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

        Arguments
        ---------
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
        Either a `Group` or a `Param` with the specified name(s). If neither is
        found, returns the default value.
        '''
        try:
            return self[group]
        except KeyError:
            return default

    def __getitem__(self, group):
        '''Get a group or parameter.

        Arguments
        ---------
        group : str
            If this string contains a period (.), then the part before the
            period will be used to retrieve a group, and the part after the
            period will be used to retrieve a parameter from that group. If this
            string does not contain a period, then just a group will be
            returned.

        Returns
        -------
        Either a `Group` or a `Param` with the specified name(s).

        Raises
        ------
        KeyError, if no group and parameter with the given identifiers are
        found.
        '''
        if isinstance(group, int):
            return super(Manager, self).__getitem__(group)
        group = group.upper()
        param = None
        if '.' in group:
            group, param = group.split('.', 1)
        group = super(Manager, self).__getitem__(group)
        if param:
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

    def get_string(self, key):
        '''Get a parameter value as a string.'''
        return self[key].string_value

    def parameter_blocks(self):
        '''Compute the size (in 512B blocks) of the parameter section.'''
        bytes = 4. + sum(g.binary_size() for g in self.itervalues())
        return int(numpy.ceil(bytes / 512))

    def frame_rate(self):
        return self.header.frame_rate

    def scale_factor(self):
        return self.get_float('POINT.SCALE')

    def points_per_frame(self):
        return self.get_uint16('POINT.USED')

    num_points = points_per_frame

    def analog_per_frame(self):
        return self.get_uint16('ANALOG.USED')

    num_analog = analog_per_frame

    def start_field(self):
        return self.get_uint32('TRIAL.ACTUAL_START_FIELD')

    def end_field(self):
        return self.get_uint32('TRIAL.ACTUAL_END_FIELD')


class Reader(Manager):
    '''This class provides methods for reading the data in a C3D file.

    A C3D file contains metadata and frame-based data describing 3D motion.

    You can iterate over the frames in the file by calling `read_frames()` after
    construction:

    >>> r = c3d.Reader(open('capture.c3d', 'rb'))
    >>> for points, analog in r.read_frames():
    ...     print('{0.shape} points in this frame'.format(points))
    ...     frames.append(points, analog)
    '''

    def __init__(self, handle):
        '''Initialize this C3D file by reading header and parameter data.

        Arguments
        ---------
        handle : file handle
            Read metadata and C3D motion frames from the given file handle. This
            handle is assumed to be `seek`-able and `read`-able. The handle must
            remain open for the life of the `Reader` instance. The `Reader` does
            not `close` the handle.

        Raises
        ------
        ValueError, if the processor metadata in the C3D file is anything other
        than 84 (Intel format).
        '''
        super(Reader, self).__init__(Header(handle))

        self._handle = handle
        self._handle.seek((self.header.parameter_block - 1) * 512)

        # metadata header
        buf = self._handle.read(4)
        _, _, parameter_blocks, processor = struct.unpack('BBBB', buf)
        if processor != 84:
            raise ValueError('We only read Intel C3D files.')

        # read all metadata in a chunk, then process each chunk (to avoid block
        # boundary issues).
        bytes = self._handle.read(512 * parameter_blocks)
        while bytes:
            buf = cStringIO.StringIO(bytes)

            chars_in_name, group_id = struct.unpack('bb', buf.read(2))
            if group_id == 0 or chars_in_name == 0:
                break

            name = buf.read(abs(chars_in_name)).upper()

            offset_to_next, = struct.unpack('h', buf.read(2))

            if group_id < 0:
                group_id = abs(group_id)
                size, = struct.unpack('B', buf.read(1))
                desc = size and buf.read(size) or ''
                if self.get(name):
                    warnings.warn('duplicate parameter group {}'.format(name))
                else:
                    self.add_group(group_id, name, desc)
            else:
                self[group_id].add_param(name, handle=buf)

            bytes = bytes[2 + abs(chars_in_name) + offset_to_next:]

    def read_frames(self):
        '''Iterate over the data frames from our C3D file handle.

        Returns
        -------
        This generates a sequence of (points, analog) ordered pairs, one
        ordered pair per frame. The first element of each frame contains a numpy
        array of 4D "points" and the second element of each frame contains a
        numpy array of 1D "analog" values that were probably recorded
        simultaneously.

        The four dimensions in the point data are typically (x, y, z) and a
        "confidence" estimate for the point.
        '''
        # find out where we seek to start reading frame data.
        start_block = self.get_uint16('POINT.DATA_START')
        if start_block != self.header.data_block:
            if not start_block:
                start_block = self.header.data_block

        # read frame and analog data in either float or int format.
        format = 'fi'[self.scale_factor() >= 0]
        ppf = self.points_per_frame()
        apf = self.analog_per_frame()

        self._handle.seek((start_block - 1) * 512)
        start = self._handle.tell()
        f = 0
        for f in xrange(self.end_field() - self.start_field() + 1):
            points = array.array(format)
            points.fromfile(self._handle, 4 * ppf)
            analog = array.array(format)
            analog.fromfile(self._handle, apf)
            yield numpy.array(points).reshape((ppf, 4)), numpy.array(analog)


class Writer(Manager):
    '''This class manages the task of writing metadata and frames to a C3D file.

    >>> r = c3d.Reader(open('data.c3d', 'rb'))
    >>> frames = smooth_frames(r.read_frames())
    >>> w = c3d.Writer(open('smoothed.c3d', 'wb'))
    >>> w.write_from_reader(frames, r)
    '''

    def __init__(self, handle):
        '''Initialize a new Writer with a file handle.

        Arguments
        ---------
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
        # header
        self.header.write(self._handle)
        self._pad_block()
        assert self._handle.tell() == 512

        # groups
        self._handle.write(struct.pack('BBBB', 0, 0, self.parameter_blocks(), 84))
        id_groups = sorted((i, g) for i, g in self.iteritems() if isinstance(i, int))
        for group_id, group in id_groups:
            self._write_group(group_id, group)

        # padding
        self._pad_block()
        while self._handle.tell() != 512 * (self.header.data_block - 1):
            self._handle.write('\x00' * 512)

    def _write_group(self, group_id, group):
        '''Write a single parameter group, with parameters, to our file handle.

        Arguments
        ---------
        group_id : int
            The numerical ID of the group.
        group : `Group`
            The `Group` object to write to the handle.
        '''
        self._handle.write(struct.pack('bb', len(group.name), -group_id))
        self._handle.write(group.name)
        self._handle.write(struct.pack('h', 3 + len(group.desc)))
        self._handle.write(struct.pack('B', len(group.desc)))
        self._handle.write(group.desc)
        for name, param in group.params.iteritems():
            self._handle.write(struct.pack('bb', len(name), group_id))
            self._handle.write(name)
            self._handle.write(struct.pack('h', param.binary_size() - 2 - len(name)))
            param.write(self._handle)

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

        Arguments
        ---------
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
        point_group.add_param('USED', desc='Number of 3d markers',
                              data_size=2,
                              bytes=struct.pack('H', ppf))
        point_group.add_param('FRAMES', desc='frame count',
                              data_size=2,
                              bytes=struct.pack('H', min(65535, frame_count)))
        point_group.add_param('DATA_START', desc='data block number',
                              data_size=2,
                              bytes=struct.pack('H', 0))
        point_group.add_param('SCALE', desc='3d scale factor',
                              data_size=4,
                              bytes=struct.pack('f', point_scale_factor))
        point_group.add_param('RATE', desc='3d data capture rate',
                              data_size=4,
                              bytes=struct.pack('f', point_frame_rate))
        point_group.add_param('X_SCREEN', desc='X_SCREEN parameter',
                              data_size=-1,
                              dimensions=[2],
                              bytes='+X')
        point_group.add_param('Y_SCREEN', desc='Y_SCREEN parameter',
                              data_size=-1,
                              dimensions=[2],
                              bytes='+Z')
        point_group.add_param('UNITS', desc='3d data units',
                              data_size=-1,
                              dimensions=[len(point_units)],
                              bytes=point_units)
        point_group.add_param('LABELS', desc='labels',
                              data_size=-1,
                              dimensions=[5, ppf],
                              bytes=''.join('M%03d ' % i for i in xrange(ppf)))
        point_group.add_param('DESCRIPTIONS', desc='descriptions',
                              data_size=-1,
                              dimensions=[16, ppf],
                              bytes=' ' * 16 * ppf)

        # ANALOG group
        apf = len(analog)
        analog_group = self.add_group(2, 'ANALOG', 'ANALOG group')
        analog_group.add_param('USED', desc='analog channel count',
                               data_size=2,
                               bytes=struct.pack('H', apf))
        analog_group.add_param('RATE', desc='analog frame rate',
                               data_size=4,
                               bytes=struct.pack('f', analog_frame_rate))
        analog_group.add_param('GEN_SCALE', desc='analog general scale factor',
                               data_size=4,
                               bytes=struct.pack('f', gen_scale))
        analog_group.add_param('SCALE', desc='analog channel scale factors',
                               data_size=4,
                               dimensions=[0])
        analog_group.add_param('OFFSET', desc='analog channel offsets',
                               data_size=2,
                               dimensions=[0])

        # TRIAL group
        trial_group = self.add_group(3, 'TRIAL', 'TRIAL group')
        trial_group.add_param('ACTUAL_START_FIELD', desc='actual start frame',
                              data_size=2,
                              dimensions=[2],
                              bytes=struct.pack('I', 1))
        trial_group.add_param('ACTUAL_END_FIELD', desc='actual end frame',
                              data_size=2,
                              dimensions=[2],
                              bytes=struct.pack('I', frame_count))

        # sync parameter information to header.
        blocks = self.parameter_blocks()
        point_group.params['DATA_START'].bytes = struct.pack('H', 2 + blocks)

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
