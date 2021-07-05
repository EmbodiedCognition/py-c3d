'''Contains the Writer class for writing C3D files.'''

import copy
import numpy as np
import struct
# import warnings
from . import utils
from .manager import Manager
from .dtypes import DataTypes


class Writer(Manager):
    '''This class writes metadata and frames to a C3D file.

    For example, to read an existing C3D file, apply some sort of data
    processing to the frames, and write out another C3D file::

    >>> r = c3d.Reader(open('data.c3d', 'rb'))
    >>> w = c3d.Writer()
    >>> w.add_frames(process_frames_somehow(r.read_frames()))
    >>> with open('smoothed.c3d', 'wb') as handle:
    >>>     w.write(handle)

    Parameters
    ----------
    point_rate : float, optional
        The frame rate of the data. Defaults to 480.
    analog_rate : float, optional
        The number of analog samples per frame. Defaults to 0.
    point_scale : float, optional
        The scale factor for point data. Defaults to -1 (i.e., "check the
        POINT:SCALE parameter").
    point_units : str, optional
        The units that the point numbers represent. Defaults to ``'mm  '``.
    gen_scale : float, optional
        General scaling factor for analog data. Defaults to 1.
    '''

    def __init__(self,
                 point_rate=480.,
                 analog_rate=0.,
                 point_scale=-1.):
        '''Set minimal metadata for this writer.

        '''
        self._dtypes = DataTypes()  # Only support INTEL format from writing
        super(Writer, self).__init__()

        # Header properties
        self._header.frame_rate = np.float32(point_rate)
        self._header.scale_factor = np.float32(point_scale)
        self.analog_rate = analog_rate
        self._frames = []

    @staticmethod
    def from_reader(reader, conversion=None):
        ''' Convert a `c3d.reader.Reader` to a persistent `c3d.writer.Writer` instance.

        Parameters
        ----------
        source : `c3d.reader.Reader`
            Source to copy data from.
        conversion : str
            Conversion mode, None is equivalent to the default mode. Supported modes are:

                'consume'       - (Default) Reader object will be
                                  consumed and explicitly deleted.

                'copy'          - Reader objects will be deep copied.

                'copy_metadata' - Similar to 'copy' but only copies metadata and
                                  not point and analog frame data.

                'copy_shallow'  - Similar to 'copy' but group parameters are
                                  not copied.

                'copy_header'   - Similar to 'copy_shallow' but only the
                                  header is copied (frame data is not copied).

        Returns
        -------
        param : `c3d.writer.Writer`
            A writeable and persistent representation of the `c3d.reader.Reader` object.

        Raises
        ------
        ValueError
            If mode string is not equivalent to one of the supported modes.
            If attempting to convert non-Intel files using mode other than 'shallow_copy'.
        '''
        writer = Writer()
        # Modes
        is_header_only = conversion == 'copy_header'
        is_meta_copy = conversion == 'copy_metadata'
        is_meta_only = is_header_only or is_meta_copy
        is_consume = conversion == 'consume' or conversion is None
        is_shallow_copy = conversion == 'shallow_copy' or is_header_only
        is_deep_copy = conversion == 'copy' or is_meta_copy
        # Verify mode
        if not (is_consume or is_shallow_copy or is_deep_copy):
            raise ValueError(
                "Unknown mode argument %s. Supported modes are: 'consume', 'copy', or 'shallow_copy'".format(
                    conversion
                ))
        if not reader._dtypes.is_ieee and not is_shallow_copy:
            # Can't copy/consume non-Intel files due to the uncertainty of converting parameter data.
            raise ValueError(
                "File was read in %s format and only 'shallow_copy' mode is supported for non Intel files!".format(
                    reader._dtypes.proc_type
                ))

        if is_consume:
            writer._header = reader._header
            writer._groups = reader._groups
        elif is_deep_copy:
            writer._header = copy.deepcopy(reader._header)
            writer._groups = copy.deepcopy(reader._groups)
        elif is_shallow_copy:
            # Only copy header (no groups)
            writer._header = copy.deepcopy(reader._header)
            # Reformat header events
            writer._header.encode_events(writer._header.events)

            # Transfer a minimal set parameters
            writer.set_start_frame(reader.first_frame)
            writer.set_point_labels(reader.point_labels)
            writer.set_analog_labels(reader.analog_labels)

            gen_scale, analog_scales, analog_offsets = reader.get_analog_transform_parameters()
            writer.set_analog_general_scale(gen_scale)
            writer.set_analog_scales(analog_scales)
            writer.set_analog_offsets(analog_offsets)

        if not is_meta_only:
            # Copy frames
            for (i, point, analog) in reader.read_frames(copy=True, camera_sum=False):
                writer.add_frames((point, analog))
        if is_consume:
            # Cleanup
            reader._header = None
            reader._groups = None
            del reader
        return writer

    @property
    def analog_rate(self):
        return super(Writer, self).analog_rate

    @analog_rate.setter
    def analog_rate(self, value):
        per_frame_rate = value / self.point_rate
        assert float(per_frame_rate).is_integer(), "Analog rate must be a multiple of the point rate."
        self._header.analog_per_frame = np.uint16(per_frame_rate)

    @property
    def numeric_key_max(self):
        ''' Get the largest numeric key.
        '''
        num = 0
        if len(self._groups) > 0:
            for i in self._groups.keys():
                if isinstance(i, int):
                    num = max(i, num)
        return num

    @property
    def numeric_key_next(self):
        ''' Get a new unique numeric group key.
        '''
        return self.numeric_key_max + 1

    def get_create(self, label):
        ''' Get or create a parameter `c3d.group.Group`.'''
        label = label.upper()
        group = self.get(label)
        if group is None:
            group = self.add_group(self.numeric_key_next, label, label + ' group')
        return group

    @property
    def point_group(self):
        ''' Get or create the POINT parameter group.'''
        return self.get_create('POINT')

    @property
    def analog_group(self):
        ''' Get or create the ANALOG parameter group.'''
        return self.get_create('ANALOG')

    @property
    def trial_group(self):
        ''' Get or create the TRIAL parameter group.'''
        return self.get_create('TRIAL')

    def add_group(self, group_id, name, desc):
        '''Add a new parameter group. See Manager.add_group() for more information.

        Returns
        -------
        group : `c3d.group.Group`
            An editable group instance.
        '''
        return super(Writer, self)._add_group(group_id, name, desc)

    def rename_group(self, *args):
        ''' Rename a specified parameter group (see Manager._rename_group for args). '''
        super(Writer, self)._rename_group(*args)

    def remove_group(self, *args):
        '''Remove the parameter group. (see Manager._rename_group for args). '''
        super(Writer, self)._remove_group(*args)

    def add_frames(self, frames, index=None):
        '''Add frames to this writer instance.

        Parameters
        ----------
        frames : Single or sequence of (point, analog) pairs
            A sequence or frame of frame data to add to the writer.
        index : int or None
            Insert the frame or sequence at the index (the first sequence frame will be inserted at the given `index`).
            Note that the index should be relative to 0 rather then the frame number provided by read_frames()!
        '''
        sh = np.shape(frames)
        # Single frame
        if len(sh) < 2:
            frames = [frames]
            sh = np.shape(frames)

        # Check data shapes match
        if len(self._frames) > 0:
            point0, analog0 = self._frames[0]
            psh, ash = np.shape(point0), np.shape(analog0)
            for f in frames:
                if np.shape(f[0]) != psh:
                    raise ValueError(
                        'Shape of analog data does not previous frames. Expexted shape {}, was {}.'.format(
                            str(psh), str(np.shape(f[0]))
                        ))
                if np.shape(f[1]) != ash:
                    raise ValueError(
                        'Shape of analog data does not previous frames. Expexted shape {}, was {}.'.format(
                            str(ash), str(np.shape(f[1]))
                        ))

        # Sequence of invalid shape
        if sh[1] != 2:
            raise ValueError(
                'Expected frame input to be sequence of point and analog pairs on form (None, 2). ' +
                'Input was of shape {}.'.format(str(sh)))

        if index is not None:
            self._frames[index:index] = frames
        else:
            self._frames.extend(frames)

    def set_point_labels(self, labels):
        ''' Set point data labels.

        Parameters
        ----------
        labels : iterable
            Set POINT:LABELS parameter entry from a set of string labels.
        '''
        grp = self.point_group
        if labels is None:
            grp.add_empty_array('LABELS', 'Point labels.')
        else:
            label_str, label_max_size = utils.pack_labels(labels)
            grp.add_str('LABELS', 'Point labels.', label_str, label_max_size, len(labels))

    def set_analog_labels(self, labels):
        ''' Set analog data labels.

        Parameters
        ----------
        labels : iterable
            Set ANALOG:LABELS parameter entry from a set of string labels.
        '''
        grp = self.analog_group
        if labels is None:
            grp.add_empty_array('LABELS', 'Analog labels.')
        else:
            label_str, label_max_size = utils.pack_labels(labels)
            grp.add_str('LABELS', 'Analog labels.', label_str, label_max_size, len(labels))

    def set_analog_general_scale(self, value):
        ''' Set ANALOG:GEN_SCALE factor (uniform analog scale factor).
        '''
        self.analog_group.set('GEN_SCALE', 'Analog general scale factor', 4, '<f', value)

    def set_analog_scales(self, values):
        ''' Set ANALOG:SCALE factors (per channel scale factor).

        Parameters
        ----------
        values : iterable or None
            Iterable containing individual scale factors (float32) for scaling analog channel data.
        '''
        if utils.is_iterable(values):
            data = np.array([v for v in values], dtype=np.float32)
            self.analog_group.set_array('SCALE', 'Analog channel scale factors', data)
        elif values is None:
            self.analog_group.set_empty_array('SCALE', 'Analog channel scale factors')
        else:
            raise ValueError('Expected iterable containing analog scale factors.')

    def set_analog_offsets(self, values):
        ''' Set ANALOG:OFFSET offsets (per channel offset).

        Parameters
        ----------
        values : iterable or None
            Iterable containing individual offsets (int16) for encoding analog channel data.
        '''
        if utils.is_iterable(values):
            data = np.array([v for v in values], dtype=np.int16)
            self.analog_group.set_array('OFFSET', 'Analog channel offsets', data)
        elif values is None:
            self.analog_group.set_empty_array('OFFSET', 'Analog channel offsets')
        else:
            raise ValueError('Expected iterable containing analog data offsets.')

    def set_start_frame(self, frame=1):
        ''' Set the 'TRIAL:ACTUAL_START_FIELD' parameter and header.first_frame entry.

        Parameters
        ----------
        frame : int
            Number for the first frame recorded in the file.
            Frame counter for a trial recording always start at 1 for the first frame.
        '''
        self.trial_group.set('ACTUAL_START_FIELD', 'Actual start frame', 2, '<I', frame, 2)
        if frame < 65535:
            self._header.first_frame = np.uint16(frame)
        else:
            self._header.first_frame = np.uint16(65535)

    def _set_last_frame(self, frame):
        ''' Sets the 'TRIAL:ACTUAL_END_FIELD' parameter and header.last_frame entry.
        '''
        self.trial_group.set('ACTUAL_END_FIELD', 'Actual end frame', 2, '<I', frame, 2)
        self._header.last_frame = np.uint16(min(frame, 65535))

    def set_screen_axis(self, X='+X', Y='+Y'):
        ''' Set the X_SCREEN and Y_SCREEN parameters in the POINT group.

        Parameters
        ----------
        X : str
            Two byte string with first character indicating positive or negative axis (+/-),
            and the second axis (X/Y/Z). Example strings '+X' or '-Y'
        Y : str
            Second axis string with same format as Y. Determines the second Y screen axis.
        '''
        if len(X) != 2:
            raise ValueError('Expected string literal to be a 2 character string for the X_SCREEN parameter.')
        if len(Y) != 2:
            raise ValueError('Expected string literal to be a 2 character string for the Y_SCREEN parameter.')
        group = self.point_group
        group.set_str('X_SCREEN', 'X_SCREEN parameter', X)
        group.set_str('Y_SCREEN', 'Y_SCREEN parameter', Y)

    def write(self, handle):
        '''Write metadata, point and analog frames to a file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        if not self._frames:
            raise RuntimeError('Attempted to write empty file.')

        points, analog = self._frames[0]
        ppf = len(points)
        apf = len(analog)

        first_frame = self.first_frame
        if first_frame <= 0:  # Bad value
            first_frame = 1
        nframes = len(self._frames)
        last_frame = first_frame + nframes - 1

        UINT16_MAX = 65535

        # POINT group
        group = self.point_group
        group.set('USED', 'Number of point samples', 2, '<H', ppf)
        group.set('FRAMES', 'Total frame count', 2, '<H', min(UINT16_MAX, nframes))
        if nframes >= UINT16_MAX:
            # Should be floating point
            group.set('LONG_FRAMES', 'Total frame count', 4, '<f', nframes)
        elif 'LONG_FRAMES' in group:
            # Docs states it should not exist if frame_count < 65535
            group.remove_param('LONG_FRAMES')
        group.set('DATA_START', 'First data block containing frame samples.', 2, '<H', 0)
        group.set('SCALE', 'Point data scaling factor', 4, '<f', self.point_scale)
        group.set('RATE', 'Point data sample rate', 4, '<f', self.point_rate)
        # Optional
        if 'UNITS' not in group:
            group.add_str('UNITS', 'Units used for point data measurements.', 'mm')
        if 'DESCRIPTIONS' not in group:
            group.add_str('DESCRIPTIONS', 'Channel descriptions.', '  ' * ppf, 2, ppf)

        # ANALOG group
        group = self.analog_group
        group.set('USED', 'Analog channel count', 2, '<H', apf)
        group.set('RATE', 'Analog samples per second', 4, '<f', self.analog_rate)
        if 'GEN_SCALE' not in group:
            self.set_analog_general_scale(1.0)
        # Optional
        if 'SCALE' not in group:
            self.set_analog_scales(None)
        if 'OFFSET' not in group:
            self.set_analog_offsets(None)
        if 'DESCRIPTIONS' not in group:
            group.add_str('DESCRIPTIONS', 'Channel descriptions.', '  ' * apf, 2, apf)

        # TRIAL group
        self.set_start_frame(first_frame)
        self._set_last_frame(last_frame)

        # sync parameter information to header.
        start_block = self.parameter_blocks() + 2
        self.get('POINT:DATA_START').bytes = struct.pack('<H', start_block)
        self._header.data_block = np.uint16(start_block)
        self._header.point_count = np.uint16(ppf)
        self._header.analog_count = np.uint16(np.prod(np.shape(analog)))

        self._write_metadata(handle)
        self._write_frames(handle)

    def _pad_block(self, handle):
        '''Pad the file with 0s to the end of the next block boundary.'''
        extra = handle.tell() % 512
        if extra:
            handle.write(b'\x00' * (512 - extra))

    def _write_metadata(self, handle):
        '''Write metadata to a file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        self._check_metadata()

        # Header
        self._header.write(handle)
        self._pad_block(handle)
        assert handle.tell() == 512

        # Groups
        handle.write(struct.pack(
            'BBBB', 0, 0, self.parameter_blocks(), self._dtypes.processor))
        for group_id, group in self.listed():
            group._data.write(group_id, handle)

        # Padding
        self._pad_block(handle)
        while handle.tell() != 512 * (self.header.data_block - 1):
            handle.write(b'\x00' * 512)

    def _write_frames(self, handle):
        '''Write our frame data to the given file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        assert handle.tell() == 512 * (self._header.data_block - 1)
        scale_mag = abs(self.point_scale)
        is_float = self.point_scale < 0
        if is_float:
            point_dtype = self._dtypes.float32
            point_scale = 1.0
        else:
            point_dtype = self._dtypes.int16
            point_scale = scale_mag
        raw = np.zeros((self.point_used, 4), point_dtype)

        analog_scales, analog_offsets = self.get_analog_transform()
        analog_scales_inv = 1.0 / analog_scales

        for points, analog in self._frames:
            # Transform point data
            valid = points[:, 3] >= 0.0
            raw[~valid, 3] = -1
            raw[valid, :3] = points[valid, :3] / point_scale
            raw[valid, 3] = np.bitwise_or(np.rint(points[valid, 3] / scale_mag).astype(np.uint8),
                                          (points[valid, 4].astype(np.uint16) << 8),
                                          dtype=np.uint16)

            # Transform analog data
            analog = analog * analog_scales_inv + analog_offsets
            analog = analog.T

            # Write
            analog = analog.astype(point_dtype)
            handle.write(raw.tobytes())
            handle.write(analog.tobytes())
        self._pad_block(handle)
