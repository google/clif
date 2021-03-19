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
from absl.testing import parameterized

from clif.testing.python import smart_ptrs
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import smart_ptrs_pybind11
except ImportError:
  smart_ptrs_pybind11 = None
# pylint: enable=g-import-not-at-top


class Add(smart_ptrs.Operation):

  def __init__(self, a, b):
    smart_ptrs.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b


class AddPybind11(object if smart_ptrs_pybind11 is None else
                  smart_ptrs_pybind11.Operation):

  def __init__(self, a, b):
    smart_ptrs_pybind11.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b


def AddParameterized(wrapper_lib):
  return AddPybind11 if wrapper_lib is smart_ptrs_pybind11 else Add


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (smart_ptrs, smart_ptrs_pybind11))
    if np[1] is not None
])
class SmartPtrsTest(absltest.TestCase):

  def testSmartPtrs(self, wrapper_lib):
    a = wrapper_lib.A()
    a.a = 123
    b = wrapper_lib.B()
    b.Set(a)
    self.assertEqual(b.Get().a, 123)
    self.assertEqual(b.GetNew().a, 123)

    # |a| is not shared with C++. So, the below call to Func should invalidate
    # it.
    b = wrapper_lib.Func(a)
    self.assertEqual(b.Get().a, 123)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      wrapper_lib.Func(a)

    a = wrapper_lib.A()
    a.a = 54321
    b.SetSP(a)
    # |a| is shared between C++ and Python. So, cannot give it to Func.
    with self.assertRaises(ValueError):
      wrapper_lib.Func(a)

    # Check |a| is intact.
    self.assertEqual(a.a, 54321)

    # Remove the reference in |b|
    b.Set(a)
    # We should be able to call Func again
    b = wrapper_lib.Func(a)
    self.assertEqual(b.Get().a, 54321)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      wrapper_lib.Func(a)

    add = AddParameterized(wrapper_lib)(120, 3)
    self.assertEqual(wrapper_lib.PerformUP(add), 123)
    # Previous call to Perform invalidated |add|
    with self.assertRaises(ValueError):
      wrapper_lib.PerformUP(add)

    add = AddParameterized(wrapper_lib)(1230, 4)
    self.assertEqual(wrapper_lib.PerformSP(add), 1234)
    # Calls to PerformSP should not invalidate |add|.
    self.assertEqual(wrapper_lib.PerformSP(add), 1234)

    self.assertEqual(wrapper_lib.D1(123).Get(), 123)

  def testPrivateDtor(self, wrapper_lib):
    # Can deal with objects with private/protected destructor std::shared_ptr.
    d = wrapper_lib.WithPrivateDtor.New()
    self.assertEqual(d.Get(), 321)

  def testF3(self, wrapper_lib):
    x = wrapper_lib.X()
    x.y = 123
    x1 = wrapper_lib.F3(x)
    self.assertEqual(x1.y, 123)
    with self.assertRaises(ValueError):
      _ = x.y

  def testInfiniteLoopAddRun(self, wrapper_lib):
    # No leak (manually verified under cl/362141489).
    add = AddParameterized(wrapper_lib)
    while True:
      add(1, 2).Run()
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopPerformSP(self, wrapper_lib):
    # No leak (manually verified under cl/362141489).
    add = AddParameterized(wrapper_lib)
    while True:
      self.assertEqual(wrapper_lib.PerformSP(add(19, 29)), 48)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopPerformUP(self, wrapper_lib):
    # No leak (manually verified under cl/362141489).
    if wrapper_lib is not smart_ptrs:
      return  # pybind11 raises a ValueError (exercised above).
    add = AddParameterized(wrapper_lib)
    while True:
      self.assertEqual(wrapper_lib.PerformUP(add(17, 23)), 40)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopRunStashedSPOperation(self, wrapper_lib):
    # No leak (manually verified under cl/362141489).
    add = AddParameterized(wrapper_lib)
    while True:
      s = wrapper_lib.OperationStashSP()
      s.Stash(add(13, 29))
      self.assertEqual(s.RunStashed(), 42)
      return  # Comment out for manual leak checking (use `top` command).

  def testInfiniteLoopRunStashedUPOperation(self, wrapper_lib):
    # No leak (manually verified under cl/362141489).
    if wrapper_lib is not smart_ptrs:
      return  # pybind11 raises a ValueError (exercised above).
    add = AddParameterized(wrapper_lib)
    while True:
      s = wrapper_lib.OperationStashUP()
      s.Stash(add(31, 59))
      self.assertEqual(s.RunStashed(), 90)
      return  # Comment out for manual leak checking (use `top` command).


if __name__ == '__main__':
  absltest.main()
