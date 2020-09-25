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

"""Tests for clif.examples.wrappod.python.wrappod."""

import unittest
from wrappod.python import wrappod


class WrappodTest(unittest.TestCase):

  def testMyClass(self):
    obj = wrappod.MyClass()

    self.assertTrue(hasattr(obj, 'a'))
    self.assertIsInstance(obj.a, int)

    self.assertTrue(hasattr(obj, 'f'))
    self.assertIsInstance(obj.f, float)

    self.assertTrue(hasattr(obj, 's'))
    self.assertIsInstance(obj.s, bytes)

    self.assertTrue(hasattr(obj, 'my_pair'))
    self.assertIsInstance(obj.my_pair, tuple)

    # The field "v" of the C++ class is not visible in Python. However,
    # "unproperty" getter and setter methods are available in Python.
    self.assertFalse(hasattr(obj, 'v'))
    self.assertIsInstance(obj.getv(), list)

    # The "unproperty" method getv returns only a copy of the C++ value.
    l = obj.getv()
    self.assertEqual(len(l), 0)
    l.append(1)
    self.assertEqual(len(l), 1)
    self.assertEqual(len(obj.getv()), 0)

    obj.setv([1, 2, 3])
    self.assertEqual(len(obj.getv()), 3)
    l = obj.getv()
    self.assertEqual(len(l), 3)
    l.append(4)
    self.assertEqual(len(l), 4)
    self.assertEqual(len(obj.getv()), 3)

    # The field 'd' of the C++ class MyClass is not visible in Python.
    self.assertFalse(hasattr(obj, 'd'))


if __name__ == '__main__':
  unittest.main()
