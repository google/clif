# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for clif.testing.python.std_containers."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import std_containers


class StdContainersTest(parameterized.TestCase):

  @parameterized.parameters(
      (std_containers.PassVectorInt, 0), (std_containers.PassArrayInt2, 1)
  )
  def testPassVectorInt(self, fn, offset):
    self.assertEqual(fn([7, 13]), 140 + offset)
    self.assertEqual(fn({6, 2}), 116 + offset)
    self.assertEqual(fn({'x': 8, 'y': 11}.values()), 138 + offset)
    self.assertEqual(fn({3: None, 9: None}.keys()), 124 + offset)
    self.assertEqual(fn(i for i in [4, 17]), 142 + offset)
    self.assertEqual(fn(map(lambda i: i * 3, [8, 7])), 190 + offset)
    with self.assertRaises(TypeError):
      fn({'x': 0, 'y': 1})
    with self.assertRaises(TypeError):
      fn({})

  def testPassVectorPairInt(self):
    fn = std_containers.PassVectorPairInt
    self.assertEqual(fn(zip([5, 17], [13, 9])), 2222)

  def testPassSetInt(self):
    fn = std_containers.PassSetInt
    self.assertEqual(fn({3, 15}), 254)
    self.assertEqual(fn({5: None, 12: None}.keys()), 251)
    with self.assertRaises(TypeError):
      fn([])
    with self.assertRaises(TypeError):
      fn({})
    with self.assertRaises(TypeError):
      fn({}.values())
    with self.assertRaises(TypeError):
      fn(i for i in [])

  def testVector(self):
    self.assertEqual(std_containers.Mul([1, 2, 3], 2), [2, 4, 6])

  def testArrayDiv(self):
    self.assertEqual(std_containers.Div([2, 4], 2), [1, 2])

    error = ValueError
    if 'pybind11' in std_containers.__doc__:
      error = TypeError
    # Exceed bounds of array.
    self.assertRaises(error, lambda: std_containers.Div([2, 4, 6], 2))

  def testArrayTranspose(self):
    self.assertEqual(
        std_containers.Transpose([[1, 2, 3], [4, 5, 6]]),
        [[1, 4], [2, 5], [3, 6]])

  def testVectorBool(self):
    self.assertEqual(std_containers.Odd([1, 2, 3]), [True, False, True])
    self.assertEqual(std_containers.Even([1, 2, 3]), [False, True, False])

  def testMap(self):
    # pylint: disable=bad-whitespace
    self.assertEqual(std_containers.Find(0, {1: 2, 3: 4, 5: 0}), (True, 5))
    r = std_containers.Find(6, {1: 2, 3: 4, 5: 0})
    self.assertIsInstance(r, tuple)
    self.assertIs(r[0], False)

  def testOnes(self):
    ones = std_containers.Ones(4, 5)
    self.assertLen(ones, 4)
    for row in ones:
      self.assertLen(row, 5)
      self.assertTrue(all(elem == 1 for elem in row))

  def testCapitals(self):
    capitals = std_containers.Capitals()
    self.assertLen(capitals, 3)
    self.assertEqual(capitals[0], ('CA', 'Sacramento'))
    self.assertEqual(capitals[1], ('OR', 'Salem'))
    self.assertEqual(capitals[2], ('WA', 'Olympia'))

  def testConcatAllListListStr(self):
    f = std_containers.ConcatAllListListStr
    self.assertEqual(f([]), '')
    self.assertEqual(f([[]]), '$')
    self.assertEqual(f([[], []]), '$$')
    self.assertEqual(f([['a']]), 'a,$')
    self.assertEqual(f([['a'], ['b']]), 'a,$b,$')
    self.assertEqual(f([['a', 'b']]), 'a,b,$')
    with self.assertRaises(TypeError):
      f([-1])

  def testMatrixSum(self):
    a = [[1, 2, 3], [3, 2, 1]]
    b = [[4, 3, 2], [2, 3, 4]]
    s = std_containers.MatrixSum(a, b)
    self.assertLen(s, 2)
    for row in s:
      self.assertLen(row, 3)
      self.assertTrue(all(elem == 5 for elem in row))

  def testMake2By3(self):
    m = std_containers.Make2By3()
    self.assertLen(m, 2)
    for c in m:
      self.assertLen(c, 3)

  def testFlatten2By3(self):
    m = ((1, 2, 3), (4, 5, 6))
    self.assertLen(m, 2)
    t = std_containers.Flatten2By3(m)
    self.assertLen(t, 6)
    for e, i in zip(t, range(1, 7)):
      self.assertEqual(e, i)

  def testTakeVectorOfStrings(self):
    self.assertEqual(
        std_containers.LastStringInVector(['hello', 'world']), 'world')

  def testContainerWithSmartPointers(self):
    v = [1, 2, 3]
    self.assertCountEqual(v, std_containers.unique_ptr_vector_round_trip(v))
    m = {1: 2, 3: 4, 5: 6}
    self.assertDictEqual(
        m, std_containers.unique_ptr_unordered_map_round_trip(m))
    s = {1, 2, 3}
    self.assertCountEqual(
        s, std_containers.unique_ptr_unordered_set_round_trip(s))
    # TODO: Implement type casters for smart pointers with tuples.
    # p = (1, 2)
    # self.assertCountEqual(p, std_containers.unique_ptr_pair_round_trip(p))

  def testContainerWithCustomizedHash(self):
    my_map = std_containers.create_unordered_map_customized_hash()
    self.assertEqual(
        std_containers.consume_unordered_map_customized_hash(my_map), 2)
    my_set = std_containers.create_unordered_set_customized_hash()
    self.assertEqual(
        std_containers.consume_unordered_set_customized_hash(my_set), 2)

  @absltest.skipIf(
      'pybind11' not in std_containers.__doc__,
      'Legacy PyCLIF does not accept None as smart pointers.')
  def testAcceptNoneAsSmartPointers(self):
    self.assertIsNone(std_containers.unique_ptr_vector_round_trip(None))
    self.assertIsNone(std_containers.unique_ptr_unordered_map_round_trip(None))
    self.assertIsNone(std_containers.unique_ptr_unordered_set_round_trip(None))


if __name__ == '__main__':
  absltest.main()
