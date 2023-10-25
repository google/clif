# Copyright 2023 Google LLC
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

import io

from absl.testing import absltest

from clif.python import callback_exception_guard
from clif.testing.python import pyobject_ptr as tst


# For use as a temporary user-defined object, to maximize sensitivity of the
# tests below.
class PyValueHolder:

  def __init__(self, value):
    self.value = value


class PyObjectPtrTest(absltest.TestCase):

  def test_return_pyobject_ptr(self):
    obj = tst.return_pyobject_ptr()
    self.assertEqual(obj, 2314)

  def test_pass_pyobject_ptr(self):
    self.assertTrue(tst.pass_pyobject_ptr(()))
    self.assertFalse(tst.pass_pyobject_ptr({}))

  def test_call_callback_with_pyobject_ptr_return(self):

    def cb(cvh):
      if cvh.value == 0:
        return PyValueHolder(10)
      if cvh.value == 1:
        return PyValueHolder("One")
      raise ValueError(f"Unknown cvh.value: {cvh.value}")

    cc = tst.call_callback_with_pyobject_ptr_return
    for _ in range(1000):
      self.assertEqual(cc(cb, tst.CppValueHolder(0)).value, 10)
    for _ in range(1000):
      self.assertEqual(cc(cb, tst.CppValueHolder(1)).value, "One")
    for _ in range(1000):
      with self.assertRaisesRegex(ValueError, r"^Unknown cvh\.value: 2$"):
        cc(cb, tst.CppValueHolder(2))

  def test_call_callback_with_pyobject_ptr_arg(self):

    sio = io.StringIO()

    def cb(pvh):
      if pvh.value == 20:
        return tst.CppValueHolder(100)
      if pvh.value == "Two":
        return tst.CppValueHolder(101)
      raise ValueError(f"Unknown pvh.value: {pvh.value}")

    cc = tst.call_callback_with_pyobject_ptr_arg
    # Without the for loops ASAN did not reliably detect heap-use-after-free
    # when there was a reference count bug in clif/python/stltypes.h.
    for _ in range(1000):
      self.assertEqual(cc(cb, PyValueHolder(20)).value, 100)
    for _ in range(1000):
      self.assertEqual(cc(cb, PyValueHolder("Two")).value, 101)
    if "pybind11" in tst.__doc__:
      for _ in range(1000):
        with self.assertRaisesRegex(ValueError, r"^Unknown pvh\.value: 3\.0$"):
          cc(cb, PyValueHolder(3.0))
    elif tst.cpp_exceptions_enabled():  # OSS (github.com/google/clif)
      for _ in range(1000):
        with self.assertRaisesRegex(
            RuntimeError,
            r"^C\+\+ exception: ValueError: Unknown pvh\.value: 3\.0$",
        ):
          cc(cb, PyValueHolder(3.0))
    else:
      cb_guarded = callback_exception_guard.print_and_clear(
          substitute_return_value=tst.CppValueHolder(-123), file=sio
      )(cb)
      for _ in range(1000):
        self.assertEqual(cc(cb_guarded, PyValueHolder(3.0)).value, -123)
      self.assertIn("ValueError: Unknown pvh.value: 3.0", sio.getvalue())

  def test_call_callback_with_pyobject_ptr_int_args_temporary_arg(self):
    def cb(pvh, num):
      return tst.CppValueHolder(pvh.value * 10 + num)

    cc = tst.call_callback_with_pyobject_ptr_int_args
    for _ in range(1000):
      self.assertEqual(cc(cb, PyValueHolder(30)).value, 340)

  def test_call_callback_with_pyobject_ptr_int_args_named_arg(self):
    def cb(pvh, num):
      return tst.CppValueHolder(pvh.value * 10 + num)

    cc = tst.call_callback_with_pyobject_ptr_int_args
    value_holder = PyValueHolder(30)
    for _ in range(1000):
      self.assertEqual(cc(cb, value_holder).value, 340)

  def test_call_callback_with_int_pyobject_ptr_args_temporary_arg(self):
    def cb(num, pvh):
      return tst.CppValueHolder(num * 20 + pvh.value)

    cc = tst.call_callback_with_int_pyobject_ptr_args
    for _ in range(1000):
      self.assertEqual(cc(cb, PyValueHolder(60)).value, 1060)

  def test_call_callback_with_int_pyobject_ptr_args_named_arg(self):
    def cb(num, pvh):
      return tst.CppValueHolder(num * 20 + pvh.value)

    cc = tst.call_callback_with_int_pyobject_ptr_args
    value_holder = PyValueHolder(60)
    for _ in range(1000):
      self.assertEqual(cc(cb, value_holder).value, 1060)


if __name__ == "__main__":
  absltest.main()
