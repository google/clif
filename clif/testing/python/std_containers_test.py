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
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import std_containers_pybind11
except ImportError:
  std_containers_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (std_containers,
                                             std_containers_pybind11))
    if np[1] is not None
])
class StdContainersTest(absltest.TestCase):

  def testVector(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Mul([1, 2, 3], 2), [2, 4, 6])

  def testArray(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Div([2, 4], 2), [1, 2])

    error = ValueError
    if wrapper_lib is std_containers_pybind11:
      error = TypeError
    # Exceed bounds of array.
    self.assertRaises(error, lambda: wrapper_lib.Div([2, 4, 6], 2))

  def testVectorBool(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Odd([1, 2, 3]), [True, False, True])
    self.assertEqual(wrapper_lib.Even([1, 2, 3]), [False, True, False])

  def testMap(self, wrapper_lib):
    # pylint: disable=bad-whitespace
    self.assertEqual(wrapper_lib.Find(0, {1: 2, 3: 4, 5: 0}), (True, 5))
    r = wrapper_lib.Find(6, {1: 2, 3: 4, 5: 0})
    self.assertIsInstance(r, tuple)
    self.assertIs(r[0], False)

  def testOnes(self, wrapper_lib):
    ones = wrapper_lib.Ones(4, 5)
    self.assertLen(ones, 4)
    for row in ones:
      self.assertLen(row, 5)
      self.assertTrue(all(elem == 1 for elem in row))

  def testCapitals(self, wrapper_lib):
    capitals = wrapper_lib.Capitals()
    self.assertLen(capitals, 3)
    self.assertEqual(capitals[0], ('CA', 'Sacramento'))
    self.assertEqual(capitals[1], ('OR', 'Salem'))
    self.assertEqual(capitals[2], ('WA', 'Olympia'))

  def testMatrixSum(self, wrapper_lib):
    a = [[1, 2, 3], [3, 2, 1]]
    b = [[4, 3, 2], [2, 3, 4]]
    s = wrapper_lib.MatrixSum(a, b)
    self.assertLen(s, 2)
    for row in s:
      self.assertLen(row, 3)
      self.assertTrue(all(elem == 5 for elem in row))

  def testMake2By3(self, wrapper_lib):
    m = wrapper_lib.Make2By3()
    self.assertLen(m, 2)
    for c in m:
      self.assertLen(c, 3)

  def testFlatten2By3(self, wrapper_lib):
    m = ((1, 2, 3), (4, 5, 6))
    self.assertLen(m, 2)
    t = wrapper_lib.Flatten2By3(m)
    self.assertLen(t, 6)
    for e, i in zip(t, range(1, 7)):
      self.assertEqual(e, i)

  def testTakeVectorOfStrings(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.LastStringInVector(['hello', 'world']), 'world')


if __name__ == '__main__':
  absltest.main()
