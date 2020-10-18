import numpy as np
import warnings


def count_nan(array):
    return np.sum(np.isnan(array))

##
#
#   Functions evaluting logical expressions on input parameters (returns True/False)
#
##
def array_has_values(array):
    ''' Returns true if at least one dimension in the array is 0
    '''
    return np.prod(np.shape(array)) > 0


def values_in_range(array, min_range, max_range):
    ''' Returns true if values in the array are within the (min, max) range.
    '''
    return np.all((min_range < array) & (array < max_range))


##
#
#   Functions asserting properties on input parameters
#
##
def array_match_headers(point, analog, reader, label):
    ''' Check point and analog arrays as fetched from load_data(reader), matches the headers in the reader.
    '''
    assert reader.point_used == np.shape(point)[1],\
        'Mismatch in number of POINT samples for file {}, read {} expected {}'.format(
         np.shape(point)[1], reader.point_used)
    assert reader.analog_used == np.shape(analog)[1],\
        'Mismatch in number of ANALOG samples for file {}, read {} expected {}'.format(
         np.shape(analog)[1], reader.analog_used)


def point_data_in_range(point, label, min_range, max_range):
    ''' Asserts if all columns in POINT data are within the given range.
    '''
    # Mask in relation to camera bits
    assert array_has_values(point), 'No registered camera bits for file {}'.format(label)
    for i in range(5):
        assert values_in_range(point[:, i], min_range, max_range),\
                "POINT data for column {} was not in range ({}, {}) for file '{}'. Was in range ({}, {})".format(
                i, min_range, max_range, label, np.min(point), np.max(point))


def analog_data_in_range(analog, label, min_range, max_range):
    ''' Asserts if all values in analog are within the given range.
    '''
    # Check ANALOG data
    assert values_in_range(analog, min_range, max_range),\
            "ANALOG data was not in range ({}, {}) for file '{}'. Was in range ({}, {})".format(
            min_range, max_range, label, np.min(analog), np.max(analog))


def equal_headers(test_label, areader, breader, alabel, blabel, areal, breal):
    ''' Ensure headers for data in reader a & b are equivalent.
    '''

    aheader = areader.header
    bheader = breader.header
    assert aheader.parameter_block == bheader.parameter_block, \
        '{}, parameter_block: {} {}, {} {}'.format(test_label,
        alabel, aheader.parameter_block, blabel, bheader.parameter_block)
    assert aheader.parameter_block == bheader.parameter_block, \
        '{}, data_block: {} {}, {} {}'.format(test_label,
        alabel, aheader.data_block, blabel, bheader.data_block)
    assert aheader.point_count == bheader.point_count, \
        '{}, point_count: {} {}, {} {}'.format(test_label,
        alabel, aheader.point_count, blabel, bheader.point_count)
    assert aheader.analog_count == bheader.analog_count, \
        '{}, analog_count: {} {}, {} {}'.format(test_label,
        alabel, aheader.point_count, blabel, bheader.point_count)
    assert aheader.first_frame == bheader.first_frame, \
        '{}, point_count: {} {}, {} {}'.format(test_label,
        alabel, aheader.first_frame, blabel, bheader.first_frame)
    assert aheader.last_frame == bheader.last_frame, \
        '{}, last_frame: {} {}, {} {}'.format(test_label,
        alabel, aheader.last_frame, vbheader.last_frame)
    assert aheader.analog_per_frame == bheader.analog_per_frame, \
        '{}, analog_per_frame: {} {}, {} {}'.format(test_label,
        alabel, aheader.analog_per_frame, blabel, bheader.analog_per_frame)
    assert aheader.frame_rate == bheader.frame_rate, \
        '{}, frame_rate: {} {}, {} {}'.format(test_label,
        alabel, aheader.frame_rate, blabel, bheader.frame_rate)
    assert aheader.max_gap == bheader.max_gap, \
        '{}, max_gap: {} {}, {} {}'.format(test_label,
        alabel, aheader.max_gap, blabel, bheader.max_gap)
    assert aheader.max_gap == bheader.max_gap, \
        '{}, max_gap: {} {}, {} {}'.format(test_label,
        alabel, aheader.max_gap, blabel, bheader.max_gap)
    assert aheader.long_event_labels == bheader.long_event_labels, \
        '{}, long_event_labels: {} {}, {} {}'.format(test_label,
        alabel, aheader.long_event_labels, blabel, bheader.long_event_labels)

    event_mismatch = max(0, bheader.event_count - aheader.event_count)
    for i in range(aheader.event_count):
        event_label = aheader.event_labels[i]
        if event_label in bheader.event_labels:
            lindex = bheader.event_labels.index(event_label)
            assert aheader.event_disp_flags[i] == bheader.event_disp_flags[lindex], \
                '{}, event_disp_flag {}: {} {}, {} {}'.format(test_label, event_label,
                alabel, aheader.event_disp_flags[i], blabel, bheader.event_disp_flags[lindex])
            assert np.isclose(aheader.event_timings[i], bheader.event_timings[lindex], atol=1e-7), \
                '{}, event_timings {}: {} {}, {} {}'.format(test_label, event_label,
                alabel, aheader.event_timings[i], blabel, bheader.event_timings[lindex])
        else:
            event_mismatch += 1

    # Validate event differences, up to a few labels can be mismatched
    err_str = '''{}, label missmatch in event_block. File {} had {} and {} had {} with no match'''.format(
        test_label, alabel, [l for l in aheader.event_labels if l not in bheader.event_labels],
        blabel, [l for l in bheader.event_labels  if l not in aheader.event_labels])
    if event_mismatch > 0:
        if event_mismatch <= 2:
            warnings.warn(err_str, ImportWarning)
        else:
            assert False, err_str


    if areal:
        assert aheader.scale_factor < 0.0, \
            '{}, {} scale_factor: expected {} < 0'.format(test_label, alabel, aheader.scale_factor)
    else:
        assert aheader.scale_factor > 0.0, \
            '{}, {} scale_factor: expected 0 < {}'.format(test_label, alabel, aheader.scale_factor)
    if breal:
        assert bheader.scale_factor < 0.0, \
            '{}, {} scale_factor: expected {} < 0'.format(test_label, blabel, bheader.scale_factor)
    else:
        assert bheader.scale_factor > 0.0, \
            '{}, {} scale_factor: expected 0 < {}'.format(test_label, blabel, bheader.scale_factor)
