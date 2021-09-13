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

from absl.testing import absltest

from clif.testing.python import smart_ptrs


class Add(smart_ptrs.Operation):

  def __init__(self, a, b):
    smart_ptrs.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b


class SmartPtrsTest(absltest.TestCase):

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

  def testInfiniteLoopAddRun(self):
    # No leak (manually verified under cl/362141489).
    while True:
      Add(1, 2).Run()
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopPerformSP(self):
    # No leak (manually verified under cl/362141489).
    while True:
      self.assertEqual(smart_ptrs.PerformSP(Add(19, 29)), 48)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopPerformUP(self):
    # No leak (manually verified under cl/362141489).
    if 'pybind11' in smart_ptrs.__doc__:
      return  # pybind11 raises a ValueError (exercised above).
    while True:
      self.assertEqual(smart_ptrs.PerformUP(Add(17, 23)), 40)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopRunStashedSPOperation(self):
    # No leak (manually verified under cl/362141489).
    while True:
      s = smart_ptrs.OperationStashSP()
      s.Stash(Add(13, 29))
      self.assertEqual(s.RunStashed(), 42)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopRunStashedUPOperation(self):
    # No leak (manually verified under cl/362141489).
    if 'pybind11' in smart_ptrs.__doc__:
      return  # pybind11 raises a ValueError (exercised above).
    while True:
      s = smart_ptrs.OperationStashUP()
      s.Stash(Add(31, 59))
      self.assertEqual(s.RunStashed(), 90)
      return  # Comment out for manual leak checking (use `top` command).


if __name__ == '__main__':
  absltest.main()
