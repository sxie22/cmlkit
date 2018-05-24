from unittest import TestCase
from unittest.mock import MagicMock
import os
from qmmltools.dataset import *
import numpy as np

dirname = os.path.dirname(os.path.abspath(__file__))

z = np.array([[1, 2, 3], [1, 2, 3]])
r = np.array([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], [[0.0, 0.1, 0.0], [1.0, 0.0, 0.0], [0.0, 1.1, 0.0]]])
b = None
name = 'test'
desc = 'just a test'
p = {'e': np.array([1.0, 1.1])}
info = compute_dataset_info(z, r, p)

d = {
    'name': name,
    'desc': desc,
    'z': z,
    'r': r,
    'b': b,
    'p': p,
    'info': info,
    'n': 2,
    'id': name,
    'family': name
}


class TestDataset(TestCase):
    def setUp(self):
        self.d = d

    def test_from_dict(self):

        dataset = Dataset.from_dict(self.d)

        self.assertEqual(dataset.z.all(), self.d['z'].all())
        self.assertEqual(dataset.r.all(), self.d['r'].all())
        self.assertEqual(dataset.b, self.d['b'])
        self.assertEqual(dataset.p['e'].all(), self.d['p']['e'].all())
        self.assertEqual(dataset.name, self.d['name'])
        self.assertEqual(dataset.desc, self.d['desc'])
        self.assertEqual(dataset.info, self.d['info'])
        self.assertEqual(dataset.id, self.d['id'])
        self.assertEqual(dataset.family, self.d['family'])


    def test_fails_if_different_size(self):

        d2 = self.d.copy()
        d2['z'] = d['z'][1]

        self.assertRaises(Exception, Dataset.from_dict, d2)

        d2 = self.d.copy()
        d2['b'] = d['z'][1]

        self.assertRaises(Exception, Dataset.from_dict, d2)

        d2 = self.d.copy()
        d2['r'] = []

        self.assertRaises(Exception, Dataset.from_dict, d2)


    def test_from_file(self):
        d2 = read(dirname + '/test.dat.npy')

        self.assertEqual(d2.z.all(), self.d['z'].all())
        self.assertEqual(d2.r.all(), self.d['r'].all())
        self.assertEqual(d2.b, self.d['b'])
        self.assertEqual(d2.p['e'].all(), self.d['p']['e'].all())
        self.assertEqual(d2.name, self.d['name'])
        self.assertEqual(d2.desc, self.d['desc'])
        self.assertEqual(d2.id, self.d['id'])
        self.assertEqual(d2.family, self.d['family'])


class TestSubset(TestCase):

    def setUp(self):
        dataset = Dataset.from_dict(d)
        self.sub = Subset(dataset, [1], name='sub', desc='test subset')

    def test_works_as_expected(self):
        self.assertEqual(self.sub.z.all(), np.array([[[1, 2, 3]]]).all())
        self.assertEqual(self.sub.r.all(), np.array([[[0.0, 0.1, 0.0], [1.0, 0.0, 0.0], [0.0, 1.1, 0.0]]]).all())
        self.assertEqual(self.sub.p['e'].all(), np.array([1.1]).all())
        self.assertEqual(self.sub.n, 1)
        self.assertEqual(self.sub.name, 'sub')
        self.assertEqual(self.sub.id, 'test-sub')

    def test_from_dict(self):
        d2 = {
            'name': self.sub.name,
            'desc': self.sub.desc,
            'id': self.sub.id,
            'z': self.sub.z,
            'r': self.sub.r,
            'b': self.sub.b,
            'p': self.sub.p,
            'info': self.sub.info,
            'parent_info': self.sub.parent_info,
            'n': 1,
            'idx': [1],
            'family': 'test'
        }

        sub2 = Subset.from_dict(d2)

        self.assertEqual(sub2.z.all(), d2['z'].all())
        self.assertEqual(sub2.r.all(), d2['r'].all())
        self.assertEqual(sub2.b, d2['b'])
        self.assertEqual(sub2.p['e'].all(), d2['p']['e'].all())
        self.assertEqual(sub2.name, d2['name'])
        self.assertEqual(sub2.desc, d2['desc'])
        self.assertEqual(sub2.parent_info['name'], d2['parent_info']['name'])
        self.assertEqual(sub2.idx, d2['idx'])

    def test_from_file(self):
        sub = read(dirname + '/test-sub.dat.npy')
        print(sub.id)
        self.assertEqual(sub.z.all(), self.sub.z.all())
        self.assertEqual(sub.r.all(), self.sub.r.all())
        self.assertEqual(sub.b, self.sub.b)
        self.assertEqual(sub.p['e'].all(), self.sub.p['e'].all())
        self.assertEqual(sub.name, self.sub.name)
        self.assertEqual(sub.desc, self.sub.desc)
        self.assertEqual(sub.id, self.sub.id)
        self.assertEqual(sub.idx, self.sub.idx)


class TestView(TestCase):

    def test_works_as_expected(self):
        dataset = Dataset.from_dict(d)
        v = dataset[np.arange(1)]

        self.assertEqual(v.z.all(), np.array([[[1, 2, 3]]]).all())
        self.assertEqual(v.r.all(), np.array([[[0.0, 0.1, 0.0], [1.0, 0.0, 0.0], [0.0, 1.1, 0.0]]]).all())
        self.assertEqual(v.p['e'].all(), np.array([1.1]).all())
