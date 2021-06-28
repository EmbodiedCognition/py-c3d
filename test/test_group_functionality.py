import unittest
import c3d
import numpy as np
import test.verify as verify
from test.zipload import Zipload
from test.base import Base

class GroupSample():
    ''' Verify groups persist. '''
    def __init__(self, manager):
        self.manager = manager
        self.sample()

    @property
    def group_items(self):
        '''Helper to access group items. '''
        return [(k, g) for (k, g) in self.manager.group_items]

    @property
    def group_list(self):
        '''Helper to access group numerical key-value pairs. '''
        return [(k, g) for (k, g) in self.manager.group_listed]

    @property
    def fetch_groups(self):
        return self.group_items, self.group_list

    def sample(self):
        '''Call before applying changes. '''
        self.s_grp_items, self.s_grp_list = self.fetch_groups

    def assert_entry_count(self):
        '''Assert all values in group still exist. '''
        grp_items, grp_list = self.fetch_groups

        assert len(self.s_grp_items) == len(grp_items),\
            'Rename added item entry. Had %i entries, now has %i.' % (len(self.s_grp_items), len(grp_items))
        assert len(self.s_grp_list) == len(grp_list),\
            'Rename added list entry. Had %i entries, now has %i.' % (len(self.s_grp_list), len(grp_list))
        assert len(grp_items) == len(grp_list),\
            'Mismatch in the number of numerical and name keys. Had %i entries, now has %i.' %\
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
        for i, (n, g), (n2, g2) in zip(enumerator, self.s_grp_list, self.group_list):
            assert n == n2, 'Group string id missmatch after changes for entry %i. ' % i +\
                            'Initially %i, after change entry was %i' % (n, n2)
            assert g == g2, 'Group listed order changed for entry %i.' % i


class Sample00(Base):
    ZIP = 'sample01.zip'
    INTEL_INT = 'Eb015pi.c3d'
    INTEL_REAL = 'Eb015pr.c3d'

    def test_Group_group_items(self):
        '''Test Group.group_items'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_keys = [k for (k, g) in reader.group_items]
        assert len(grp_keys) > 0, 'No group items in file or Group.group_items failed'

    def test_Group_group_listed(self):
        '''Test Group.group_listed'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_list = [k for (k, g) in reader.group_listed]
        assert len(grp_list) > 0, 'No group items in file or Group.group_listed  failed'

    def test_Group_rename_group(self):
        '''Test if renaming groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_keys = [k for (k, g) in reader.group_items]
        ref = GroupSample(reader)

        for i, key in enumerate(grp_keys):
            test_name = 'TEST_NAME' + str(i)

            grp = reader.get(key)
            reader.rename_group(key, test_name)
            grp2 = reader.get(test_name)

            assert grp2 is not None, "Rename failed, group with name '%s' does not exist."
            assert grp == grp2, 'Rename failed, group acquired from new name is not identical.'

        ref.assert_entry_count()
        ref.assert_group_list()

    def test_Group_renumber_group(self):
        '''Test if renaming (renumbering) groups acts as intended.'''
        reader = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        grp_ids = [k for (k, g) in reader.group_listed]
        ref = GroupSample(reader)

        max_key = np.max(grp_ids)

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
            raise RuntimeError('Overwriting existing numerical ID should raise a ValueError.')
        except KeyError as e:
            pass # Correct





if __name__ == '__main__':
    unittest.main()
