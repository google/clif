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

"""Tests for clif.testing.python.callback."""

from absl.testing import absltest
from absl.testing import parameterized
import six

from clif.testing.python import callback
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import callback_pybind11
except ImportError:
  callback_pybind11 = None
# pylint: enable=g-import-not-at-top


def Callback(input_data):
  return 0, input_data


def Callback2(input_data):
  return input_data


def InvalidCallback1():
  return 0


def InvalidCallback2(a, b, c):  # pylint: disable=unused-argument
  return 0


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (callback, callback_pybind11))
    if np[1] is not None
])
class CallbackTest(absltest.TestCase):

  def CallbackMethod(self, data):
    return 1, data

  def CallbackInvalid(self, wrapper_lib):
    self.assertIsNotNone(wrapper_lib)
    return 2

  def testNewStyleConstRef(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.NewStyleCallbackConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      wrapper_lib.NewStyleCallbackConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      wrapper_lib.NewStyleCallbackConstRef(13, InvalidCallback2)

  def testNewStyleNonConstRef(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.NewStyleCallbackNonConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      wrapper_lib.NewStyleCallbackNonConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      wrapper_lib.NewStyleCallbackNonConstRef(13, InvalidCallback2)

  def testNewStyleConstRefWithSelfCallback(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.NewStyleCallbackConstRef([2, 3], self.CallbackMethod),
        [2, 3])
    with self.assertRaises(TypeError):
      wrapper_lib.NewStyleCallbackConstRef(23, self.CallbackInvalid)

  def testSelfCallback(self, wrapper_lib):
    # assert not raises:
    wrapper_lib.SelfCallback(Callback)

  def testStrCallback(self, wrapper_lib):
    def cb(s):
      self.assertIsInstance(s, six.text_type)
      self.assertEqual(s, 'foo')

    wrapper_lib.StringCallback(cb)

  def testCallableOutput(self, wrapper_lib):
    returned_callback = wrapper_lib.FunctionWithCallableReturn(Callback2)
    self.assertEqual(returned_callback(5), 5)


if __name__ == '__main__':
  absltest.main()
