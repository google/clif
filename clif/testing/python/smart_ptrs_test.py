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

"""Tests for clif.testing.python.smart_ptrs."""

import unittest
from clif.testing.python import smart_ptrs


class Add(smart_ptrs.Operation):

  def __init__(self, a, b):
    smart_ptrs.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b


class SmartPtrsTest(unittest.TestCase):

  def testSmartPtrs(self):
    a = smart_ptrs.A()
    a.a = 123
    b = smart_ptrs.B()
    b.Set(a)
    self.assertEqual(b.Get().a, 123)
    self.assertEqual(b.GetNew().a, 123)

    # |a| is not shared with C++. So, the below call to Func should invalidate
    # it.
    b = smart_ptrs.Func(a)
    self.assertEqual(b.Get().a, 123)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      smart_ptrs.Func(a)

    a = smart_ptrs.A()
    a.a = 54321
    b.SetSP(a)
    # |a| is shared between C++ and Python. So, cannot give it to Func.
    with self.assertRaises(ValueError):
      smart_ptrs.Func(a)

    # Check |a| is intact.
    self.assertEqual(a.a, 54321)

    # Remove the reference in |b|
    b.Set(a)
    # We should be able to call Func again
    b = smart_ptrs.Func(a)
    self.assertEqual(b.Get().a, 54321)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      smart_ptrs.Func(a)

    add = Add(120, 3)
    self.assertEqual(smart_ptrs.PerformUP(add), 123)

    # Previous call to Perform invalidated |add|
    with self.assertRaises(ValueError):
      smart_ptrs.PerformUP(add)

    add = Add(1230, 4)
    self.assertEqual(smart_ptrs.PerformSP(add), 1234)
    # Calls to PerformSP should not invalidate |add|.
    self.assertEqual(smart_ptrs.PerformSP(add), 1234)

    self.assertEqual(smart_ptrs.D1(123).Get(), 123)

  def testF3(self):
    x = smart_ptrs.X()
    x.y = 123
    x1 = smart_ptrs.F3(x)
    self.assertEqual(x1.y, 123)
    with self.assertRaises(ValueError):
      _ = x.y


if __name__ == '__main__':
  unittest.main()
