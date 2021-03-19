# Copyright 2021 Google LLC
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

"""Tests for clif.pybind11.staging.smart_ptrs."""

import unittest
from clif.pybind11.staging import smart_ptrs


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
    # pybind11 (with smart_holder) deliberatly does not support this
    # inherently unsafe transfer of ownership.
    with self.assertRaises(ValueError) as ctx:
      smart_ptrs.PerformUP(add)
    self.assertEqual(
        str(ctx.exception),
        'Alias class (also known as trampoline) does not inherit from'
        ' py::virtual_overrider_self_life_support, therefore the'
        ' ownership of this instance cannot safely be transferred to C++.')

    add = Add(1230, 4)
    self.assertEqual(smart_ptrs.PerformSP(add), 1234)
    # Calls to PerformSP should not invalidate |add|.
    self.assertEqual(smart_ptrs.PerformSP(add), 1234)

    self.assertEqual(smart_ptrs.D1(123).Get(), 123)

  def testPrivateDtor(self):
    # Can deal with objects with private/protected destructor std::shared_ptr.
    d = smart_ptrs.WithPrivateDtor.New()
    self.assertEqual(d.Get(), 321)

  def testF3(self):
    x = smart_ptrs.X()
    x.y = 123
    x1 = smart_ptrs.F3(x)
    self.assertEqual(x1.y, 123)
    with self.assertRaises(ValueError):
      _ = x.y


if __name__ == '__main__':
  unittest.main()
