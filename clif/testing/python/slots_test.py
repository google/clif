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

"""Tests for clif.testing.python.slots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from clif.testing.python import slots


class SlotsTest(unittest.TestCase):

  def testObjectMethods(self):
    a = slots.I5()
    self.assertEqual(hash(a), 0)

  def testRO(self):
    a = slots.I5()
    self.assertEqual(len(a), 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    with self.assertRaises(NotImplementedError):
      del a[1]

  def testRW(self):
    a = slots.Z5()
    self.assertEqual(len(a), 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    del a[1]
    self.assertEqual(list(a), [0]*5)

  def testHashSmallInt(self):
    a = slots.I5()
    a[2] = 3
    a[4] = 5
    self.assertEqual(hash(a), 8)

  def testHashSsizetOverflow(self):
    a = slots.I5()
    a[0] = 999
    self.assertNotEqual(hash(a), 999)

  def testUnHashable(self):
    a = slots.Z5()
    with self.assertRaises(TypeError) as ctx:
      hash(a)
    self.assertEqual(str(ctx.exception), '__hash__ must return int')


if __name__ == '__main__':
  unittest.main()
