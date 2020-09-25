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

"""Tests for clif.examples.wrapmethod.python.wrapmethod.
"""

import unittest
from wrapmethod.python import wrapmethod


class WrapmethodTest(unittest.TestCase):

  def testMethods(self):
    obj = wrapmethod.ClassWithMethods(10)
    self.assertEqual(obj.Size(), 10)

    for i in range(obj.Size()):
      obj.Set(i, i * i)
    for i in range(obj.Size()):
      self.assertEqual(obj.Get(i), i * i)
    for i in range(obj.Size()):
      obj[i] = i * i * i
    for i in range(obj.Size()):
      self.assertEqual(obj[i], i * i * i)

    self.assertEqual(len(obj), obj.Size())
    c = 0
    for i in obj:
      self.assertEqual(c * c * c, i)
      c += 1

    l1 = lambda: obj[100]
    self.assertRaises(IndexError, l1)

    l2 = lambda: obj[-100]
    self.assertRaises(IndexError, l2)

    del obj[5]
    self.assertEqual(len(obj), 9)

    obj = wrapmethod.ClassWithMethods.ConstructWithInitVal(123, 1234)
    self.assertEqual(obj.Size(), 123)
    self.assertEqual(obj.Get(100), 1234)

    self.assertEqual(wrapmethod.ClassWithMethods.GetStaticNumber(), 54321)
    self.assertEqual(wrapmethod.GetStaticNumber(), 54321)


if __name__ == '__main__':
  unittest.main()
