''' Manager base class defining common attributes for both Reader and Writer instances.
'''
import numpy as np
import warnings
from .header import Header
from .group import GroupData, GroupReadonly, Group
from .utils import is_integer, is_iterable


class Manager(object):
    '''A base class for managing C3D file metadata.

    This class manages a C3D header (which contains some stock metadata fields)
    as well as a set of parameter groups. Each group is accessible using its
    name.

    Attributes
    ----------
    header : `c3d.header.Header`
        Header information for the C3D file.
    '''

    def __init__(self, header=None):
        '''Set up a new Manager with a Header.'''
        self._header = header or Header()
        self._groups = {}

    def __contains__(self, key):
        return key in self._groups

    def items(self):
        ''' Get iterable over pairs of (str, `c3d.group.Group`) entries.
        '''
        return ((k, v) for k, v in self._groups.items() if isinstance(k, str))

    def values(self):
        ''' Get iterable over `c3d.group.Group` entries.
        '''
        return (v for k, v in self._groups.items() if isinstance(k, str))

    def keys(self):
        ''' Get iterable over parameter name keys.
        '''
        return (k for k in self._groups.keys() if isinstance(k, str))

    def listed(self):
        ''' Get iterable over pairs of (int, `c3d.group.Group`) entries.
        '''
        return sorted((i, g) for i, g in self._groups.items() if isinstance(i, int))

    def _check_metadata(self):
        ''' Ensure that the metadata in our file is self-consistent. '''
        assert self._header.point_count == self.point_used, (
            'inconsistent point count! {} header != {} POINT:USED'.format(
                self._header.point_count,
                self.point_used,
            ))

        assert self._header.scale_factor == self.point_scale, (
            'inconsistent scale factor! {} header != {} POINT:SCALE'.format(
                self._header.scale_factor,
                self.point_scale,
            ))

        assert self._header.frame_rate == self.point_rate, (
            'inconsistent frame rate! {} header != {} POINT:RATE'.format(
                self._header.frame_rate,
                self.point_rate,
            ))

        if self.point_rate:
            ratio = self.analog_rate / self.point_rate
        else:
            ratio = 0
        assert self._header.analog_per_frame == ratio, (
            'inconsistent analog rate! {} header != {} analog-fps / {} point-fps'.format(
                self._header.analog_per_frame,
                self.analog_rate,
                self.point_rate,
            ))

        count = self.analog_used * self._header.analog_per_frame
        assert self._header.analog_count == count, (
            'inconsistent analog count! {} header != {} analog used * {} per-frame'.format(
                self._header.analog_count,
                self.analog_used,
                self._header.analog_per_frame,
            ))

        try:
            start = self.get_uint16('POINT:DATA_START')
            if self._header.data_block != start:
                warnings.warn('inconsistent data block! {} header != {} POINT:DATA_START'.format(
                    self._header.data_block, start))
        except AttributeError:
            warnings.warn('''no pointer available in POINT:DATA_START indicating the start of the data block, using
                             header pointer as fallback''')

        def check_parameters(params):
            for name in params:
                if self.get(name) is None:
                    warnings.warn('missing parameter {}'.format(name))

        if self.point_used > 0:
            check_parameters(('POINT:LABELS', 'POINT:DESCRIPTIONS'))
        else:
            lab = self.get('POINT:LABELS')
            if lab is None:
                warnings.warn('No point data found in file.')
            elif lab.num_elements > 0:
                warnings.warn('No point data found in file, but file contains POINT:LABELS entries')
        if self.analog_used > 0:
            check_parameters(('ANALOG:LABELS', 'ANALOG:DESCRIPTIONS'))
        else:
            lab = self.get('ANALOG:LABELS')
            if lab is None:
                warnings.warn('No analog data found in file.')
            elif lab.num_elements > 0:
                warnings.warn('No analog data found in file, but file contains ANALOG:LABELS entries')

    def _add_group(self, group_id, name=None, desc=None):
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
        group : :class:`Group`
            A group with the given ID, name, and description.

        Raises
        ------
        TypeError
            Input arguments are of the wrong type.
        KeyError
            Name or numerical key already exist (attempt to overwrite existing data).
        '''
        if not is_integer(group_id):
            raise TypeError('Expected Group numerical key to be integer, was %s.' % type(group_id))
        if not isinstance(name, str):
            if name is not None:
                raise TypeError('Expected Group name key to be string, was %s.' % type(name))
        else:
            name = name.upper()
        group_id = int(group_id)  # Asserts python int
        if group_id in self._groups:
            raise KeyError('Group with numerical key {} already exists'.format(group_id))
        if name in self._groups:
            raise KeyError('No group matched name key {}'.format(name))
        group = self._groups[name] = self._groups[group_id] = Group(GroupData(self._dtypes, name, desc))
        return group

    def _remove_group(self, group_id):
        '''Remove the parameter group.

        Parameters
        ----------
        group_id : int, or str
            The numeric or name ID key for a group to remove all entries for.
        '''
        grp = self._groups.get(group_id, None)
        if grp is None:
            return
        gkeys = [k for (k, v) in self._groups.items() if v == grp]
        for k in gkeys:
            del self._groups[k]

    def _rename_group(self, group_id, new_group_id):
        ''' Rename a specified parameter group.

        Parameters
        ----------
        group_id : int, str, or 'Group'
            Group instance, name, or numerical identifier for the group.
        new_group_id : str, or int
            If string, it is the new name for the group. If integer, it will replace its numerical group id.

        Raises
        ------
        KeyError
            If a group with a duplicate ID or name already exists.
        '''
        if isinstance(group_id, GroupReadonly):
            grp = group_id._data
        else:
            # Aquire instance using id
            grp = self._groups.get(group_id, None)
            if grp is None:
                raise KeyError('No group found matching the identifier: %s' % str(group_id))
        if new_group_id in self._groups:
            if new_group_id == group_id:
                return
            raise ValueError('Key %s for group %s already exist.' % (str(new_group_id), grp.name))

        # Clear old id
        if isinstance(new_group_id, (str, bytes)):
            if grp.name in self._groups:
                del self._groups[grp.name]
            grp.name = new_group_id
        elif is_integer(new_group_id):
            new_group_id = int(new_group_id)  # Ensure python int
            del self._groups[group_id]
        else:
            raise KeyError('Invalid group identifier of type: %s' % str(type(new_group_id)))
        # Update
        self._groups[new_group_id] = grp

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
        value : `c3d.group.Group` or `c3d.parameter.Param`
            Either a group or parameter with the specified name(s). If neither
            is found, returns the default value.
        '''
        if is_integer(group):
            group = self._groups.get(int(group))
            if group is None:
                return default
            return group
        group = group.upper()
        param = None
        if '.' in group:
            group, param = group.split('.', 1)
        if ':' in group:
            group, param = group.split(':', 1)
        if group not in self._groups:
            return default
        group = self._groups[group]
        if param is not None:
            return group.get(param, default)
        return group

    @property
    def header(self) -> '`c3d.header.Header`':
        ''' Access to .c3d header data. '''
        return self._header

    def parameter_blocks(self) -> int:
        '''Compute the size (in 512B blocks) of the parameter section.'''
        bytes = 4. + sum(g._data.binary_size for g in self._groups.values())
        return int(np.ceil(bytes / 512))

    @property
    def point_rate(self) -> float:
        ''' Number of sampled 3D coordinates per second. '''
        try:
            return self.get_float('POINT:RATE')
        except AttributeError:
            return self.header.frame_rate

    @property
    def point_scale(self) -> float:
        ''' Scaling applied to non-float data. '''
        try:
            return self.get_float('POINT:SCALE')
        except AttributeError:
            return self.header.scale_factor

    @property
    def point_used(self) -> int:
        ''' Number of sampled 3D point coordinates per frame. '''
        try:
            return self.get_uint16('POINT:USED')
        except AttributeError:
            return self.header.point_count

    @property
    def analog_used(self) -> int:
        ''' Number of analog measurements, or channels, for each analog data sample. '''
        try:
            return self.get_uint16('ANALOG:USED')
        except AttributeError:
            per_frame = self.header.analog_per_frame
            if per_frame > 0:
                return int(self.header.analog_count / per_frame)
            return 0

    @property
    def analog_rate(self) -> float:
        '''  Number of analog data samples per second. '''
        try:
            return self.get_float('ANALOG:RATE')
        except AttributeError:
            return self.header.analog_per_frame * self.point_rate

    @property
    def analog_per_frame(self) -> int:
        '''  Number of analog frames per 3D frame (point sample). '''
        return int(self.analog_rate / self.point_rate)

    @property
    def analog_sample_count(self) -> int:
        ''' Number of analog samples per channel. '''
        has_analog = self.analog_used > 0
        return int(self.frame_count * self.analog_per_frame) * has_analog

    @property
    def point_labels(self) -> list:
        ''' Labels for each POINT data channel. '''
        return self.get('POINT:LABELS').string_array

    @property
    def analog_labels(self) -> list:
        ''' Labels for each ANALOG data channel. '''
        return self.get('ANALOG:LABELS').string_array

    @property
    def frame_count(self) -> int:
        ''' Number of frames recorded in the data. '''
        return self.last_frame - self.first_frame + 1  # Add 1 since range is inclusive [first, last]

    @property
    def first_frame(self) -> int:
        ''' Trial frame corresponding to the first frame recorded in the data. '''
        # Start frame seems to be less of an issue to determine.
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self.get('TRIAL:ACTUAL_START_FIELD')
        if param is not None:
            # ACTUAL_START_FIELD is encoded in two 16 byte words...
            return param.uint32_value
        return self.header.first_frame

    @property
    def last_frame(self) -> int:
        ''' Trial frame corresponding to the last frame recorded in the data (inclusive). '''
        # Number of frames can be represented in many formats, first check if valid header values
        if self.header.first_frame < self.header.last_frame and self.header.last_frame != 65535:
            return self.header.last_frame

        # Check different parameter options where the frame can be encoded
        end_frame = [self.header.last_frame, 0.0, 0.0, 0.0]
        param = self.get('TRIAL:ACTUAL_END_FIELD')
        if param is not None:
            # Encoded as 2 16 bit words (rather then 1 32 bit word)
            #words = param.uint16_array
            #end_frame[1] = words[0] + words[1] * 65536
            end_frame[1] = param.uint32_value
        param = self.get('POINT:LONG_FRAMES')
        if param is not None:
            # 'Should be' encoded as float
            if param.bytes_per_element >= 4:
                end_frame[2] = int(param.float_value)
            else:
                end_frame[2] = param.uint16_value
        param = self.get('POINT:FRAMES')
        if param is not None:
            # Can be encoded either as 32 bit float or 16 bit uint
            if param.bytes_per_element == 4:
                end_frame[3] = int(param.float_value)
            else:
                end_frame[3] = param.uint16_value
        # Return the largest of the all (queue bad reading...)
        return int(np.max(end_frame))

    def get_screen_xy_strings(self):
        ''' Get the POINT:X_SCREEN and POINT:Y_SCREEN parameters as strings.

        See `Manager.get_screen_xy_axis` to get numpy vectors instead.

        Returns
        -------
        value : (str, str) or None
            Touple containing X_SCREEN and Y_SCREEN strings, or None (if no parameters could be found).
        '''
        X = self.get('POINT:X_SCREEN')
        Y = self.get('POINT:Y_SCREEN')
        if X and Y:
            return (X.string_value, Y.string_value)
        return None

    def get_screen_xy_axis(self):
        ''' Get the POINT:X_SCREEN and POINT:Y_SCREEN parameters as unit row vectors.

        Z axis can be computed using the cross product:

        \[ z = x \\times y \]

        To move a point coordinate $p_s$ as read from `c3d.reader.Reader.read_frames` out of the system basis do:

        \[ p = | x^T y^T z^T |^T p_s  \]


        See `Manager.get_screen_xy_strings` to get the parameter as string values instead.

        Returns
        -------
        value : ([3,], [3,]) or None
            Touple $(x, y)$ containing X_SCREEN and Y_SCREEN as row vectors, or None.
        '''
        # Axis conversion dictionary.
        AXIS_DICT = {
            'X': np.array([1.0, 0, 0]),
            '+X': np.array([1.0, 0, 0]),
            '-X': np.array([-1.0, 0, 0]),
            'Y': np.array([0, 1.0, 0]),
            '+Y': np.array([0, 1.0, 0]),
            '-Y': np.array([0, -1.0, 0]),
            'Z': np.array([0, 0, 1.0]),
            '+Z': np.array([0, 0, 1.0]),
            '-Z': np.array([0, 0, -1.0]),
        }

        val = self.get_screen_xy_strings()
        if val is None:
            return None
        axis_x, axis_y  = val

        # Interpret using both X/Y_SCREEN
        return AXIS_DICT[axis_x], AXIS_DICT[axis_y]


    def get_analog_transform_parameters(self):
        ''' Parse analog data transform parameters. '''
        # Offsets
        analog_offsets = np.zeros((self.analog_used), int)
        param = self.get('ANALOG:OFFSET')
        if param is not None and param.num_elements > 0:
            analog_offsets[:] = param.int16_array[:self.analog_used]

        # Scale factors
        analog_scales = np.ones((self.analog_used), float)
        gen_scale = 1.
        param = self.get('ANALOG:GEN_SCALE')
        if param is not None:
            gen_scale = param.float_value
        param = self.get('ANALOG:SCALE')
        if param is not None and param.num_elements > 0:
            analog_scales[:] = param.float_array[:self.analog_used]

        return gen_scale, analog_scales, analog_offsets

    def get_analog_transform(self):
        ''' Get broadcastable analog transformation parameters.
        '''
        gen_scale, analog_scales, analog_offsets = self.get_analog_transform_parameters()
        analog_scales *= gen_scale
        analog_scales = np.broadcast_to(analog_scales[:, np.newaxis], (self.analog_used, self.analog_per_frame))
        analog_offsets = np.broadcast_to(analog_offsets[:, np.newaxis], (self.analog_used, self.analog_per_frame))
        return analog_scales, analog_offsets

    def get_int8(self, key):
        '''Get a parameter value as an 8-bit signed integer.'''
        return self.get(key).int8_value

    def get_uint8(self, key):
        '''Get a parameter value as an 8-bit unsigned integer.'''
        return self.get(key).uint8_value

    def get_int16(self, key):
        '''Get a parameter value as a 16-bit signed integer.'''
        return self.get(key).int16_value

    def get_uint16(self, key):
        '''Get a parameter value as a 16-bit unsigned integer.'''
        return self.get(key).uint16_value

    def get_int32(self, key):
        '''Get a parameter value as a 32-bit signed integer.'''
        return self.get(key).int32_value

    def get_uint32(self, key):
        '''Get a parameter value as a 32-bit unsigned integer.'''
        return self.get(key).uint32_value

    def get_float(self, key):
        '''Get a parameter value as a 32-bit float.'''
        return self.get(key).float_value

    def get_bytes(self, key):
        '''Get a parameter value as a byte string.'''
        return self.get(key).bytes_value

    def get_string(self, key):
        '''Get a parameter value as a string.'''
        return self.get(key).string_value
