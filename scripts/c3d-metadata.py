#!/usr/bin/env python

'''Display C3D group and parameter information.'''

from __future__ import print_function

import argparse
import sys
try:
    import c3d
except ModuleNotFoundError:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..\\'))
    import c3d

parser = argparse.ArgumentParser(description='Display C3D group and parameter information.')
parser.add_argument('input', default='-', metavar='FILE', nargs='+',
                    help='process C3D data from this input FILE')


def print_metadata(reader):
    print('Header information:\n{}'.format(reader.header))
    for key, g in sorted(reader.items()):
        print('')
        for key, p in sorted(g.items()):
            print_param(g, p)


def print_param(g, p):
    print('{0.name}.{1.name}: {1.total_bytes}B {1.dimensions}'.format(g, p))

    if len(p.dimensions) == 0:
        val = None
        width = p.total_bytes
        if width == 2:
            val = p.int16_value
        elif width == 4:
            val = p.float_value
        else:
            val = p.int8_value
        print('{0.name}.{1.name} = {2}'.format(g, p, val))

    if len(p.dimensions) == 1 and p.dimensions[0] > 0:
        arr = []
        width = p.total_bytes // p.dimensions[0]
        if width == 2:
            arr = p.int16_array
        elif width == 4:
            arr = p.float_array
        else:
            arr = p.int8_array
        for r, v in enumerate(arr):
            print('{0.name}.{1.name}[{2}] = {3}'.format(g, p, r, v))

    if len(p.dimensions) == 2:
        C, R = p.dimensions
        for r in range(R):
            print('{0.name}.{1.name}[{2}] = {3}'.format(
                g, p, r, repr(p.bytes_value[r * C:(r+1) * C])))


def main(args):
    for filename in args.input:
        try:
            if filename == '-':
                print('*** (stdin) ***')
                print_metadata(c3d.Reader(sys.stdin))
            else:
                print('*** {} ***'.format(filename))
                with open(filename, 'rb') as handle:
                    print_metadata(c3d.Reader(handle))
        except Exception as err:
            print(err)


if __name__ == '__main__':
    main(parser.parse_args())
