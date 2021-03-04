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
    if wrapper_lib is smart_ptrs:
      # This test (and the test for `PerformSP` below) can work safely only
      # because PyCLIF leaks the reference count for `add` (use
      # testInfiniteLoopAddVirtualOverride below to reproduce the leak), which
      # keeps the Python instance alive beyond the time of transferring
      # ownership from Python to C++.
      self.assertEqual(wrapper_lib.PerformUP(add), 123)
      # Previous call to Perform invalidated |add|
      with self.assertRaises(ValueError):
        wrapper_lib.PerformUP(add)
    else:
      # pybind11 (with smart_holder) deliberatly does not support this
      # inherently unsafe transfer of ownership. (Knowingly leaking the
      # reference count is not an option.)
      with self.assertRaises(ValueError) as ctx:
        wrapper_lib.PerformUP(add)
      self.assertEqual(
          str(ctx.exception),
          'Ownership of instance with virtual overrides in Python cannot be'
          ' transferred to C++.')

    add = AddParameterized(wrapper_lib)(1230, 4)
    # This works with the C-API code generator only because the reference count
    # for `add` is leaked. It works cleanly in pybind11 after PR #2886.
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

  def testInfiniteLoopAddVirtualOverride(self, wrapper_lib):
    add = AddParameterized(wrapper_lib)
    while True:
      add(1, 2).Run()
      return  # Comment out for manual leak checking (use `top` command).


if __name__ == '__main__':
  absltest.main()
