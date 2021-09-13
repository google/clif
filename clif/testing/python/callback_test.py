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

from clif.testing.python import callback


def Callback(input_data):
  return 0, input_data


def Callback2(input_data):
  return input_data


def InvalidCallback1():
  return 0


def InvalidCallback2(a, b, c):  # pylint: disable=unused-argument
  return 0


class CallbackTest(absltest.TestCase):

  def CallbackMethod(self, data):
    return 1, data

  def CallbackInvalid(self):
    return 2

  def testNewStyleConstRef(self):
    self.assertEqual(
        callback.NewStyleCallbackConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(13, InvalidCallback2)

  def testNewStyleNonConstRef(self):
    self.assertEqual(
        callback.NewStyleCallbackNonConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackNonConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackNonConstRef(13, InvalidCallback2)

  def testNewStyleConstRefWithSelfCallback(self):
    self.assertEqual(
        callback.NewStyleCallbackConstRef([2, 3], self.CallbackMethod),
        [2, 3])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(23, self.CallbackInvalid)

  def testSelfCallback(self):
    # assert not raises:
    callback.SelfCallback(Callback)

  def testStrCallback(self):
    def Cb(s):
      self.assertIsInstance(s, str)
      self.assertEqual(s, 'foo')

    callback.StringCallback(Cb)

  def testCallableOutput(self):
    returned_callback = callback.FunctionWithCallableReturn(Callback2)
    self.assertEqual(returned_callback(5), 5)


if __name__ == '__main__':
  absltest.main()
