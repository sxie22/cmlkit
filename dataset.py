import numpy as np
import qmmlpack as qmml
import qmmltools.inout as qmtio


def read(filename):
    d = qmtio.read(filename, ext=False)

    if 'parent_info' in d.keys():
        return Subset.from_dict(d)
    else:
        return Dataset.from_dict(d)


class Dataset(object):
    """Dataset

    Represents a collection of structures/molecules with different properties,
    which can be saved to a file and loaded from it.

    Attributes:
        name: Short, unique name
        desc: Short description
        family: Indicates broad group of data this belongs to (for instance for property conversion)
        z, r, b: As required by qmmlpack (ragged arrays)
        p: Dict of properties, keys are strings, values are ndarrays
        id: Canonical name; used internally, equal to name for this class
        info: Dict of properties of this dataset
        n: Number of systems in dataset
    """

    def __init__(self, name, z, r, b=None, p={}, info=None, desc='', family=None):
        super(Dataset, self).__init__()
        self.name = name
        self.desc = desc
        self.z = z
        self.r = r
        self.b = b
        self.p = p
        self.id = name

        if info is None:
            self.info = dataset_info(z, r, b)
        else:
            self.info = info

        if family is None:
            self.family = name
        else:
            self.family = family

        self.n = self.info['number_systems']

    def __getitem__(self, idx):
        return View(self, idx)

    def print_info(self):
        i = self.info

        if self.b is None:
            print('{} finite systems (molecules)'.format(i['number_systems']))
        else:
            print('{} periodic systems (materials)'.format(i['number_systems']))
        print('elements: {} ({})'.format(' '.join([qmml.element_data(el, 'abbreviation')
                                                   for el in i['elements']]), len(i['elements'])))
        print('max #els/system: {};  max #el/system: {};  max #atoms/system: {}'.format(
            i['max_elements_per_system'], i['max_same_element_per_system'], i['max_atoms_per_system']))
        print('min dist: {:3.2f};  max dist: {:3.2f};  1/min dist: {:3.2f};  1/max dist: {:3.2f}'.format(
            i['min_distance'], i['max_distance'], 1. / i['min_distance'], 1. / i['max_distance']))

    def save(self, dirname='', filename=None):
        tosave = {
            'name': self.name,
            'desc': self.desc,
            'id': self.id,
            'family': self.family,
            'z': self.z,
            'r': self.r,
            'b': self.b,
            'p': self.p,
            'info': self.info,
            'n': self.n
        }

        if filename is None:
            qmtio.save(dirname + self.id + '.dat', tosave)
        else:
            qmtio.save(dirname + filename + '.dat', tosave)

    @classmethod
    def from_dict(cls, d):
        return cls(d['name'], d['z'], d['r'], d['b'], d['p'], d['info'], d['desc'], d['family'])


class Subset(Dataset):
    """Subset of data from a Dataset

    This class is intended to allow handling subsets of data of a large
    dataset (which might be inconvenient to handle) while still retaining
    some connection to the full dataset.

    Attributes:
        name: Name of this subset
        id: Canonical name of this subset, dataset_name-name
        family: Broad family of this subset
        z, r, b, p: As in Dataset
        info: Dataset info of this subset
        parent_info: Dict of info on parent dataset, namely name and info dict
    """

    def __init__(self, dataset, idx, name=None, desc='', restore_data=None):

        if restore_data is None:
            self.idx = idx
            z = dataset.z[idx]
            r = dataset.r[idx]
            if dataset.b is not None:
                b = dataset.b[idx]
            else:
                b = None

            sub_properties = {}

            for p, v in dataset.p.items():
                sub_properties[p] = v[idx]

            self.parent_info = {'info': dataset.info, 'desc': dataset.desc, 'name': dataset.name, 'id': dataset.id}
            

            if name is not None:
                self.name = name
            else:
                self.name = 'n' + str(self.n)

            super(Subset, self).__init__(self.name, z, r, b, sub_properties, desc=desc, family=dataset.family)

            self.id = self.parent_info['name'] + '-' + self.name

        else:
            super(Subset, self).__init__(restore_data['name'],
                                         restore_data['z'],
                                         restore_data['r'],
                                         restore_data['b'],
                                         restore_data['p'],
                                         restore_data['info'],
                                         restore_data['desc'],
                                         restore_data['family'])

            self.parent_info = restore_data['parent_info']
            self.n = restore_data['n']
            self.id = restore_data['id']
            self.idx = restore_data['idx']

    @classmethod
    def from_dict(cls, d):
        return cls(None, None, restore_data=d)

    def save(self, dirname='', filename=None):
        tosave = {
            'name': self.name,
            'desc': self.desc,
            'id': self.id,
            'z': self.z,
            'r': self.r,
            'b': self.b,
            'p': self.p,
            'info': self.info,
            'parent_info': self.parent_info,
            'n': self.n,
            'idx': self.idx,
            'family': self.family
        }

        if filename is None:
            qmtio.save(dirname + self.id + '.dat', tosave)
        else:
            qmtio.save(dirname + filename + '.dat', tosave)


class View(object):
    """View onto a Dataset

    This class is intended to be used when only parts of
    a Dataset need to be accessed, but no permanent Subset
    is required, for instance when chunking a bigger set.
    There should be no need to create instances of this class
    by hand, it gets created by Dataset.__getitem__.

    While Dataset and its subclasses are used for saving and
    loading, this one is the actual workhorse that gets consumed
    by the other machinery.

    """

    def __init__(self, dataset, idx):
        super(View, self).__init__()
        self.dataset = dataset
        self.idx = idx
        if isinstance(idx, int):
            self.n = 1
        else:
            self.n = len(idx)

    @property
    def z(self):
        return self.dataset.z[self.idx]

    @property
    def r(self):
        return self.dataset.r[self.idx]

    @property
    def b(self):
        if self.dataset.b is not None:
            return self.dataset.b[self.idx]
        else:
            return self.dataset.b

    @property
    def p(self):
        return DictView(self.dataset.p, self.idx)

    @property
    def info(self):
        return self.dataset.info

    @property
    def name(self):
        return self.dataset.name

    @property
    def id(self):
        return self.dataset.id

    @property
    def family(self):
        return self.dataset.family


class DictView(dict):
    """View on a dictionary where each value is an ndarray"""

    def __init__(self, d, idx):
        super(DictView, self).__init__(**d)
        self.d = d
        self.idx = idx

    def __getitem__(self, key):
        return self.d[key][self.idx]


def dataset_info(z, r, b=None):
    """Information about a dataset.

    Returns a dictionary containing information about a dataset.

    Parameters:
      z - atomic numbers
      r - atom coordinates, in Angstrom
      b - basis vectors for periodic systems
      verbose - if True, also prints the information

    Information:
      elements - elements occurring in dataset
      max_elements_per_system - largest number of different elements in a system
      max_same_element_per_system - largest number of same-element atoms in a system
      max_atoms_per_system - largest number of atoms in a system
      min_distance - minimum distance between atoms in a system
      max_distance - maximum distance between atoms in a system
    """
    assert len(z) == len(r)
    assert b is None or len(b) == len(z)

    i = {}

    i['number_systems'] = len(z)

    # elements
    i['elements'] = np.unique(np.asarray([a for s in z for a in s], dtype=np.int))
    i['max_elements_per_system'] = max([np.nonzero(np.bincount(s))[0].size for s in z])
    i['max_same_element_per_system'] = max([max(np.bincount(s)) for s in z])

    # systems
    i['max_atoms_per_system'] = max([len(s) for s in z])
    i['systems_per_element'] = np.asarray([np.sum([1 for m in z if el in m]) for el in range(118)], dtype=np.int)

    # distances
    assert len(r) > 0
    dists = [qmml.lower_triangular_part(qmml.distance_euclidean(rr), -1) for rr in r]
    i['min_distance'] = min([min(d) for d in dists if len(d) > 0])
    i['max_distance'] = max([max(d) for d in dists if len(d) > 0])

    return i