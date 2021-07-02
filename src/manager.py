import numpy as np
import warnings
from src.header import Header
from src.group import GroupData, GroupReadonly, GroupWritable
from src.utils import is_integer, is_iterable


class Manager(object):
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
        self._header = header or Header()
        self._groups = {}

    def __contains__(self, key):
        return key in self._groups

    def items(self):
        ''' Acquire iterable over parameter group pairs.

        Returns
        -------
        items : Touple of ((str, :class:`Group`), ...)
            Python touple containing pairs of name keys and parameter group entries.
        '''
        return ((k, GroupWritable(v)) for k, v in self._groups.items() if isinstance(k, str))

    def values(self):
        ''' Acquire iterable over parameter group entries.

        Returns
        -------
        values : Touple of (:class:`Group`, ...)
            Python touple containing unique parameter group entries.
        '''
        return (GroupWritable(v) for k, v in self._groups.items() if isinstance(k, str))

    def keys(self):
        ''' Acquire iterable over parameter group entry string keys.

        Returns
        -------
        keys : Touple of (str, ...)
            Python touple containing keys for the parameter group entries.
        '''
        return (k for k in self._groups.keys() if isinstance(k, str))

    def listed(self):
        ''' Acquire iterable over sorted numerical parameter group pairs.

        Returns
        -------
        items : Touple of ((int, :class:`Group`), ...)
            Sorted python touple containing pairs of numerical keys and parameter group entries.
        '''
        return sorted((i, GroupWritable(g)) for i, g in self._groups.items() if isinstance(i, int))

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
                raise RuntimeError()
        except AttributeError:
            warnings.warn('''no pointer available in POINT:DATA_START indicating the start of the data block, using
                             header pointer as fallback''')

        def check_parameters(params):
            for name in params:
                if self._get(name) is None:
                    warnings.warn('missing parameter {}'.format(name))

        if self.point_used > 0:
            check_parameters(('POINT:LABELS', 'POINT:DESCRIPTIONS'))
        else:
            warnings.warn('No point data found in file.')
        if self.analog_used > 0:
            check_parameters(('ANALOG:LABELS', 'ANALOG:DESCRIPTIONS'))
        else:
            warnings.warn('No analog data found in file.')

    def _add_group(self, group_id, name, desc):
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
        if not (isinstance(name, str) or name is None):
            raise TypeError('Expected Group name key to be string, was %s.' % type(name))
        group_id = int(group_id) # Asserts python int
        if group_id in self._groups:
            raise KeyError('Group with numerical key {} already exists'.format(group_id))
        name = name.upper()
        if name in self._groups:
            raise KeyError('No group matched name key {}'.format(name))
        group = self._groups[name] = self._groups[group_id] = GroupData(self._dtypes, name, desc)
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
            new_group_id = int(new_group_id) # Ensure python int
            del self._groups[group_id]
        else:
            raise KeyError('Invalid group identifier of type: %s' % str(type(new_group_id)))
        # Update
        self._groups[new_group_id] = grp

    def _get(self, group, default=None):
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
        value : :class:`Group` or :class:`Param`
            Either a group or parameter with the specified name(s). If neither
            is found, returns the default value.
        '''
        if is_integer(group):
            group = self._groups.get(int(group))
            if group is None:
                return default
            return GroupWritable(group)
        group = group.upper()
        param = None
        if '.' in group:
            group, param = group.split('.', 1)
        if ':' in group:
            group, param = group.split(':', 1)
        if group not in self._groups:
            return default
        group = GroupWritable(self._groups[group])
        if param is not None:
            return group.get(param, default)
        return group

    @property
    def header(self):
        ''' Access to .c3d header data. '''
        return self._header

    def parameter_blocks(self):
        '''Compute the size (in 512B blocks) of the parameter section.'''
        bytes = 4. + sum(g.binary_size for g in self._groups.values())
        return int(np.ceil(bytes / 512))

    @property
    def point_rate(self):
        ''' Number of sampled 3D coordinates per second. '''
        try:
            return self.get_float('POINT:RATE')
        except AttributeError:
            return self.header.frame_rate

    @property
    def point_scale(self):
        ''' Scaling applied to non-float data. '''
        try:
            return self.get_float('POINT:SCALE')
        except AttributeError:
            return self.header.scale_factor

    @property
    def point_used(self):
        ''' Number of sampled 3D point coordinates per frame. '''
        try:
            return self.get_uint16('POINT:USED')
        except AttributeError:
            return self.header.point_count

    @property
    def analog_used(self):
        ''' Number of analog measurements, or channels, for each analog data sample. '''
        try:
            return self.get_uint16('ANALOG:USED')
        except AttributeError:
            per_frame = self.header.analog_per_frame
            if per_frame > 0:
                return int(self.header.analog_count / per_frame)
            return 0

    @property
    def analog_rate(self):
        '''  Number of analog data samples per second. '''
        try:
            return self.get_float('ANALOG:RATE')
        except AttributeError:
            return self.header.analog_per_frame * self.point_rate

    @property
    def analog_per_frame(self):
        '''  Number of analog frames per 3D frame (point sample). '''
        return int(self.analog_rate / self.point_rate)

    @property
    def analog_sample_count(self):
        ''' Number of analog samples per channel. '''
        has_analog = self.analog_used > 0
        return int(self.frame_count * self.analog_per_frame) * has_analog

    @property
    def point_labels(self):
        ''' Labels for each POINT data channel. '''
        return self._get('POINT:LABELS').string_array

    @property
    def analog_labels(self):
        ''' Labels for each ANALOG data channel. '''
        return self.get('ANALOG:LABELS').string_array

    @property
    def frame_count(self):
        ''' Number of frames recorded in the data. '''
        return self.last_frame - self.first_frame + 1  # Add 1 since range is inclusive [first, last]

    @property
    def first_frame(self):
        ''' Trial frame corresponding to the first frame recorded in the data. '''
        # Start frame seems to be less of an issue to determine.
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self._get('TRIAL:ACTUAL_START_FIELD')
        if param is not None:
            # ACTUAL_START_FIELD is encoded in two 16 byte words...
            words = param.uint16_array
            return words[0] + words[1] * 65535
        return self.header.first_frame

    @property
    def last_frame(self):
        ''' Trial frame corresponding to the last frame recorded in the data (inclusive). '''
        # Number of frames can be represented in many formats, first check if valid header values
        if self.header.first_frame < self.header.last_frame and self.header.last_frame != 65535:
            return self.header.last_frame

        # Check different parameter options where the frame can be encoded
        end_frame = [self.header.last_frame, 0.0, 0.0, 0.0]
        param = self._get('TRIAL:ACTUAL_END_FIELD')
        if param is not None:
            # Encoded as 2 16 bit words (rather then 1 32 bit word)
            words = param.uint16_array
            end_frame[1] = words[0] + words[1] * 65536
            #end_frame[1] = param.uint32_value
        param = self._get('POINT:LONG_FRAMES')
        if param is not None:
            # Encoded as float
            end_frame[2] = int(param.float_value)
        param = self._get('POINT:FRAMES')
        if param is not None:
            # Can be encoded either as 32 bit float or 16 bit uint
            end_frame[3] = param._as_integer_value
        # Return the largest of the all (queue bad reading...)
        return int(np.max(end_frame))

    def get_screen_axis(self):
        ''' Get the X_SCREEN and Y_SCREEN parameters in the POINT group.

        Returns
        -------
        value : Touple on form (str, str) or None
            Touple containing X_SCREEN and Y_SCREEN strings, or None if no parameters could be found.
        '''
        X = self._get('POINT:X_SCREEN')
        Y = self._get('POINT:Y_SCREEN')
        if X and Y:
            return (X.string_value, Y.string_value)
        return None

    def get_analog_transform_parameters(self):
        ''' Parse analog data transform parameters. '''
        # Offsets
        analog_offsets = np.zeros((self.analog_used), int)
        param = self._get('ANALOG:OFFSET')
        if param is not None and param.num_elements > 0:
            analog_offsets[:] = param.int16_array[:self.analog_used]

        # Scale factors
        analog_scales = np.ones((self.analog_used), float)
        gen_scale = 1.
        param = self._get('ANALOG:GEN_SCALE')
        if param is not None:
            gen_scale = param.float_value
        param = self._get('ANALOG:SCALE')
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
        return self._get(key).int8_value

    def get_uint8(self, key):
        '''Get a parameter value as an 8-bit unsigned integer.'''
        return self._get(key).uint8_value

    def get_int16(self, key):
        '''Get a parameter value as a 16-bit signed integer.'''
        return self._get(key).int16_value

    def get_uint16(self, key):
        '''Get a parameter value as a 16-bit unsigned integer.'''
        return self._get(key).uint16_value

    def get_int32(self, key):
        '''Get a parameter value as a 32-bit signed integer.'''
        return self._get(key).int32_value

    def get_uint32(self, key):
        '''Get a parameter value as a 32-bit unsigned integer.'''
        return self._get(key).uint32_value

    def get_float(self, key):
        '''Get a parameter value as a 32-bit float.'''
        return self._get(key).float_value

    def get_bytes(self, key):
        '''Get a parameter value as a byte string.'''
        return self._get(key).bytes_value

    def get_string(self, key):
        '''Get a parameter value as a string.'''
        return self._get(key).string_value
