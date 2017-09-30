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

"""Tests for clif.testing.std_containers."""

import unittest
from clif.testing.python import std_containers


class StdContainersTest(unittest.TestCase):

  def testVector(self):
    self.assertEqual(std_containers.Mul([1, 2, 3], 2), [2, 4, 6])

  def testVectorBool(self):
    self.assertEqual(std_containers.Odd([1, 2, 3]), [True, False, True])
    self.assertEqual(std_containers.Even([1, 2, 3]), [False, True, False])

  def testMap(self):
    # pylint: disable=bad-whitespace
    self.assertEqual(std_containers.Find(0, {1:2, 3:4, 5:0}), (True, 5))
    r = std_containers.Find(6, {1:2, 3:4, 5:0})
    self.assertIsInstance(r, tuple)
    self.assertIs(r[0], False)

  def testOnes(self):
    ones = std_containers.Ones(4, 5)
    self.assertEqual(len(ones), 4)
    for row in ones:
      self.assertEqual(len(row), 5)
      self.assertTrue(all(elem == 1 for elem in row))

  def testCapitals(self):
    capitals = std_containers.Capitals()
    self.assertEqual(len(capitals), 3)
    self.assertEqual(capitals[0], ('CA', 'Sacramento'))
    self.assertEqual(capitals[1], ('OR', 'Salem'))
    self.assertEqual(capitals[2], ('WA', 'Olympia'))

  def testMatrixSum(self):
    a = [[1, 2, 3], [3, 2, 1]]
    b = [[4, 3, 2], [2, 3, 4]]
    s = std_containers.MatrixSum(a, b)
    self.assertEqual(len(s), 2)
    for row in s:
      self.assertEqual(len(row), 3)
      self.assertTrue(all(elem == 5 for elem in row))

  def testMake2By3(self):
    m = std_containers.Make2By3()
    self.assertEqual(len(m), 2)
    for c in m:
      self.assertEqual(len(c), 3)

  def testFlatten2By3(self):
    m = ((1, 2, 3), (4, 5, 6))
    self.assertEqual(len(m), 2)
    t = std_containers.Flatten2By3(m)
    self.assertEqual(len(t), 6)
    for e, i in zip(t, range(1, 7)):
      self.assertEqual(e, i)


if __name__ == '__main__':
  unittest.main()
