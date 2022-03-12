''' Purpose for this file is to verify functions associated with Manager._groups dictionary.
'''
import unittest
import c3d
import numpy as np
import test.verify as verify
from test.zipload import Zipload
from test.base import Base

class GroupSample():
    ''' Helper object to verify group entries persist or terminate properly. '''
    def __init__(self, manager):
        self.manager = manager
        self.sample()

    @property
    def group_items(self):
        '''Helper to access group items. '''
        return [(k, g) for (k, g) in self.manager.group_items()]

    @property
    def group_listed(self):
        '''Helper to access group numerical key-value pairs. '''
        return [(k, g) for (k, g) in self.manager.group_listed()]

    @property
    def fetch_groups(self):
        '''Acquire both group sets. '''
        return self.group_items, self.group_listed

    @property
    def max_key(self):
        if len(self.group_items) > 0:
            return np.max([k for (k, g) in self.group_listed])
        return 0

    def sample(self):
        '''Call before applying changes. '''
        self.s_grp_items, self.s_grp_list = self.fetch_groups


    def assert_entry_count(self, delta=0):
        '''Assert all values in group still exist.

        Arguments
        ---------
        delta:  Number of entries added (+) or removed (-) since last sample.
        '''
        grp_items, grp_list = self.fetch_groups

        assert len(self.s_grp_items) + delta == len(grp_items),\
            'Rename added item entry. Expected %i entries, now has %i.' %\
            (len(self.s_grp_items), len(grp_items))
        assert len(self.s_grp_list) + delta == len(grp_list),\
            'Rename added list entry. Expected %i entries, now has %i.' %\
            (len(self.s_grp_list) + delta, len(grp_list))
        assert len(grp_items) == len(grp_list),\
            'Mismatch in the number of numerical and name keys. Has %i numerical entries and %i name entries.' %\
            (len(grp_items), len(grp_list))

    def assert_group_items(self):
        '''Assert all named (str, Group) pairs persisted after change.'''
        enumerator = range(len(self.s_grp_items))
        for i, (n, g), (n2, g2) in zip(enumerator, sorted(self.s_grp_items), sorted(self.group_items)):
            assert n == n2, 'Group numeric id missmatch after changes for entry %i. ' % i +\
                            'Initially %i, after change entry was %i' % (n, n2)
            assert g == g2, 'Group listed order changed for entry %i.' % i

    def assert_group_list(self):
        '''Assert all numerical (int, Group) pairs persisted after change.'''
        enumerator = range(len(self.s_grp_list))
        for i, (n, g), (n2, g2) in zip(enumerator, self.s_grp_list, self.group_listed):
            assert n == n2, 'Group string id missmatch after changes for entry %i. ' % i +\
                            'Initially %i, after change entry was %i' % (n, n2)
            assert g == g2, 'Group listed order changed for entry %i.' % i

    def verify_add_group(self, N):
        '''Add N groups and verify count at each iteration.'''
        self.sample()
        max_key = self.max_key
        for i in range(1, N):
            test_name = 'TEST_ADD_GROUP_%i' % i
            self.manager.add_group(max_key + i, test_name, '')
            assert self.manager.get(test_name) is not None, 'Added group does not exist.'
            self.assert_entry_count(delta=i)

    def verify_remove_all_using_numeric(self):
        '''Remove all groups using numeric key and verify count at each iteration.'''
        self.sample()
        keys = [k for (k, g) in self.group_listed]
        for i, key in enumerate(keys):
            grp = self.manager.get(key)
            assert grp is not None, 'Expected group to exist.'
            self.manager.remove_group(key)
            assert self.manager.get(key) is None, 'Removed group persisted.'
            assert self.manager.get(grp.name) is None, 'Removed group persisted.'
            self.assert_entry_count(delta=-1 - i)

    def verify_remove_all_using_name(self):
        '''Remove all groups using name key and verify count at each iteration.'''
        self.sample()
        keys = [k for (k, g) in self.group_items]
        for i, key in enumerate(keys):
            grp = self.manager.get(key)
            assert grp is not None, 'Expected group to exist.'
            self.manager.remove_group(key)
            assert self.manager.get(key) is None, 'Removed group persisted.'
            assert self.manager.get(grp.name) is None, 'Removed group persisted.'
            self.assert_entry_count(delta=-1 - i)


class TestGroupAccessors(Base):
    ''' Tests functionality associated with editing Group entries in the Manager class.
    '''
    ZIP = 'sample01.zip'
    INTEL_INT = 'Eb015pi.c3d'
    INTEL_REAL = 'Eb015pr.c3d'

    def test_Manager_group_items(self):
        '''Test Manager.group_items'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_keys = [k for (k, g) in reader.group_items()]
        assert len(grp_keys) > 0, 'No group items in file or Manager.group_items failed'

    def test_Manager_group_listed(self):
        '''Test Manager.group_listed'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_list = [k for (k, g) in reader.group_listed()]
        assert len(grp_list) > 0, 'No group items in file or Manager.group_listed  failed'


    def test_Manager_add_group(self):
        '''Test if renaming groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        ref.verify_add_group(100)
        ref.verify_remove_all_using_numeric()

    def test_Manager_add_group_duplicated_names(self):
        '''Check that groups with the same name can be added if the option is enabled.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        test_name = "TEST_NAME"
        ref.manager.add_group(ref.max_key + 1, test_name, '')

        # Test default
        with self.assertRaises(KeyError):
            ref.manager.add_group(ref.max_key + 2, test_name, '')

        # Test with option on
        new_id = ref.max_key + 2
        ref.manager.add_group(new_id, test_name, '', rename_duplicated_groups=True)
        self.assertEqual(ref.manager._groups[new_id].name, test_name.upper() + str(new_id))

    def test_Manager_removing_group_from_numeric(self):
        '''Test if removing groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        ref.verify_remove_all_using_numeric()
        ref.verify_add_group(100)

    def test_Manager_removing_group_from_name(self):
        '''Test if removing groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        ref.verify_remove_all_using_name()
        ref.verify_add_group(100)

    def test_Manager_rename_group(self):
        '''Test if renaming groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        grp_keys = [k for (k, g) in ref.group_items]

        new_names = ['TEST_NAME' + str(i) for i in range(len(grp_keys))]

        for key, test_name in zip(grp_keys, new_names):
            grp = reader.get(key)
            reader.rename_group(key, test_name)
            grp2 = reader.get(test_name)

            assert grp2 is not None, "Rename failed, group with name '%s' does not exist."
            assert grp == grp2, 'Rename failed, group acquired from new name is not identical.'

        ref.assert_entry_count()
        ref.assert_group_list()

        try:
            reader.rename_group(new_names[0], new_names[1])
            raise RuntimeError('Overwriting existing numerical ID should raise a KeyError.')
        except ValueError as e:
            pass # Correct

    def test_Manager_renumber_group(self):
        '''Test if renaming (renumbering) groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        ref = GroupSample(reader)
        grp_ids = [k for (k, g) in ref.group_listed]

        max_key = ref.max_key

        for i, key in enumerate(grp_ids):
            test_num = max_key + i + 1

            grp = reader.get(key)
            reader.rename_group(key, test_num)
            grp2 = reader.get(test_num)

            assert grp2 is not None, "Rename failed, group with name '%s' does not exist."
            assert grp == grp2, 'Rename failed, group acquired from new name is not identical.'

        ref.assert_entry_count()
        ref.assert_group_items()

        try:
            reader.rename_group(max_key + 1, max_key + 2)
            raise RuntimeError('Overwriting existing numerical ID should raise a KeyError.')
        except ValueError as e:
            pass # Correct





if __name__ == '__main__':
    unittest.main()
