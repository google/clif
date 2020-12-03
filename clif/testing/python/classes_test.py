# Copyright 2020 Google LLC
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

"""Tests for clif.testing.python.classes."""

import unittest
from clif.testing.python import classes


class PyK(classes.Klass):
  pass


class ClassesTest(unittest.TestCase):

  def testKlass(self):
    self.assertEqual(classes.Klass.C2(), 3)
    k = classes.Klass(3)
    self.assertEqual(k.i, 3)
    self.assertEqual(k.i2, 9)
    self.assertEqual(k.Int1(), 4)
    k.i = 0
    self.assertEqual(k.i, 0)
    # AttributeError on CPython; TypeError on PyPy.
    with self.assertRaises((AttributeError, TypeError)):
      k.i2 = 0

  def testPythonDerived(self):
    k = PyK(4)
    self.assertEqual(k.i, 4)
    self.assertEqual(k.Int1(), 5)

  def testDerived(self):
    k = classes.Derived()
    self.assertEqual(k.i, 0)
    self.assertEqual(k.j, 0)
    self.assertNotIn(2, k)
    with self.assertRaises(TypeError):
      classes.Derived(1)

  def testDerivedInit(self):
    k = classes.Derived.Init(1, 2)
    self.assertEqual(k.i, 1)
    self.assertEqual(k.j, 2)


if __name__ == '__main__':
  unittest.main()
