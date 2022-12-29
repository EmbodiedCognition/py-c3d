''' Purpose for this file is to verify functions associated with Groups._params dictionary.
'''
import unittest
import c3d
import numpy as np
import test.verify as verify
from test.zipload import Zipload
from test.base import Base

class ParamSample():
    ''' Helper object to verify parameter entries persist or terminate properly. '''
    def __init__(self, group):
        assert isinstance(group, c3d.Group), 'Must pass group to ParamSample instance.'
        self.flt_range = (-1e6, 1e6)
        self.shape = (10, 2)
        self.group = group
        self.rnd = np.random.default_rng()
        self.sample()

    @property
    def items(self):
        '''Helper to access group items. '''
        return [(k, g) for (k, g) in self.group.param_items()]

    @property
    def keys(self):
        '''Helper to access group items. '''
        return [k for (k, g) in self.group.param_items()]

    def sample(self):
        '''Call before applying changes. '''
        self.s_items = self.items
        self.s_keys = self.keys

    def assert_entry_count(self, delta=0):
        '''Assert entry count.

        Arguments
        ---------
        delta:  Number of entries added (+) or removed (-) since last sample.
        '''
        items = self.items
        assert len(self.s_items) + delta == len(items),\
            'Rename added item entry. Expected %i entries, now has %i.' %\
            (len(self.s_items), len(items))

    def assert_group_items(self, ignore=None):
        '''Assert all named (str, Group) pairs persisted after change.'''
        enumerator = range(len(self.s_items))
        for i, (n, g) in enumerate(self.s_items):
            if n == ignore:
                continue
            g2 = self.group.get(n)
            assert g == g2, 'Group listed order changed for entry %i.' % i

    def verify_add_parameter(self, N):
        '''Add N parameters and verify count at each iteration.'''
        self.sample()
        for i in range(1, N):
            test_name = 'TEST_ADD_PARAM_%i' % i
            arr = self.rnd.uniform(*self.flt_range, size=self.shape).astype(np.float32)
            self.group.add_param(test_name, bytes_per_element=4, dimensions=arr.shape, bytes_data=arr.T.tobytes())
            assert self.group.get(test_name) is not None, 'Added group does not exist.'
            self.assert_group_items()

    def verify_remove_all(self):
        '''Remove all groups using name key and verify count at each iteration.'''
        self.sample()
        keys = [k for (k, g) in self.items]
        for i, key in enumerate(keys):
            grp = self.group.get(key)
            assert grp is not None, 'Expected group to exist.'
            self.group.remove_param(key)
            assert self.group.get(key) is None, 'Removed param persisted.'
            self.assert_entry_count(delta=-1 - i)


class TestParameterAccessors(Base):
    ''' Tests functionality associated with accessing and editing Paramater entries in Group objects.
    '''
    ZIP = 'sample01.zip'
    INTEL_INT = 'Eb015pi.c3d'
    INTEL_REAL = 'Eb015pr.c3d'

    def test_Group_values(self):
        '''Test Group.values()'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        for g in reader.group_values():
            assert len(g.param_values()) > 0, 'No group values in file or Group.param_values() failed'

    def test_Group_items(self):
        '''Test Group.items()'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        for g in reader.group_values():
            assert len(g.param_items()) > 0, 'No group items in file or Group.param_items() failed'

    def test_Group_add_param(self):
        '''Test if adding and groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        for g in reader.group_values():
            ref = ParamSample(g)
            ref.verify_add_parameter(100)
            ref.verify_remove_all()

    def test_Group_remove_param(self):
        '''Test if removing groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        for g in reader.group_values():
            ref = ParamSample(g)
            ref.verify_remove_all()
            ref.verify_add_parameter(100)

    def test_Group_rename_param(self):
        '''Test if renaming groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))

        for g in reader.group_values():
            ref = ParamSample(g)
            prm_keys = ref.keys
            new_names = ['TEST_NAME' + str(i) for i in range(len(prm_keys))]
            for key, nname in zip(prm_keys, new_names):
                prm = g.get(key)
                g.rename_param(key, nname)
                prm2 = g.get(nname)
                assert prm2 is not None, "Rename failed, renamed param does not exist."
                assert prm == prm2, 'Rename failed, param acquired from new name is not identical.'

            ref.assert_entry_count()
            try:
                g.rename_param(new_names[0], new_names[1])
                raise RuntimeError('Overwriting existing numerical ID should raise a ValueError.')
            except ValueError as e:
                pass # Correct




if __name__ == '__main__':
    unittest.main()
