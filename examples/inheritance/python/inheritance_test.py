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

"""Tests for clif.examples.inheritance.python.inheritance."""

import unittest
import base
import inheritance
import python_inheritance


class InheritanceTest(unittest.TestCase):

  def testBase(self):
    b = inheritance.Base(54321)
    self.assertEqual(b.GetBaseValue(), 54321)

  def testDerived1(self):
    d1 = inheritance.Derived1(54321)
    self.assertEqual(d1.GetBaseValue(), 12345)
    self.assertEqual(d1.GetDerivedValue(), 54321)

  def testDerived2(self):
    d2 = inheritance.Derived2()
    self.assertEqual(d2.GetBaseValue(), 12345)

    l = lambda: d2.GetDerivedValue
    self.assertRaises(AttributeError, l)


# Test for clif.examples.inheritance.python.python_inheritance
class PythonInheritanceTest(unittest.TestCase):

  def testBase(self):
    b = base.Base(54321)
    self.assertEqual(b.GetBaseValue(), 54321)

  def testDerived1(self):
    d1 = python_inheritance.Derived1(54321)
    self.assertEqual(d1.GetBaseValue(), 12345)
    self.assertEqual(d1.GetDerivedValue(), 54321)

  def testDerived2(self):
    d2 = python_inheritance.Derived2()
    self.assertEqual(d2.GetBaseValue(), 12345)

    l = lambda: d2.GetDerivedValue
    self.assertRaises(AttributeError, l)

if __name__ == '__main__':
  unittest.main()
